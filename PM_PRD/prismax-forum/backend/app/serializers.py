"""Turn ORM rows into API schemas, computing counts and per-viewer state."""
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from . import models, schemas


def human_date(dt: datetime) -> str:
    """e.g. 'Oct 24' — month + day, like the prototype cards."""
    return dt.strftime("%b %-d")


def human_ago(dt: datetime) -> str:
    """e.g. 'just now', '2h ago', '3d ago'."""
    now = datetime.now(timezone.utc)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    secs = max(0, (now - dt).total_seconds())
    if secs < 60:
        return "just now"
    mins = secs / 60
    if mins < 60:
        return f"{int(mins)}m ago"
    hours = mins / 60
    if hours < 24:
        return f"{int(hours)}h ago"
    days = hours / 24
    if days < 7:
        return f"{int(days)}d ago"
    weeks = days / 7
    if weeks < 5:
        return f"{int(weeks)}w ago"
    return human_date(dt)


def user_out(user: models.User) -> schemas.UserOut:
    return schemas.UserOut(
        id=user.id,
        name=user.name,
        initials=user.initials,
        email=user.email,
        avatar_color=user.avatar_color,
    )


def _like_count(db: Session, target_type: str, target_id: int) -> int:
    return db.scalar(
        select(func.count())
        .select_from(models.Like)
        .where(models.Like.target_type == target_type, models.Like.target_id == target_id)
    ) or 0


def _viewer_liked(db: Session, viewer: models.User | None, target_type: str, target_id: int) -> bool:
    if viewer is None:
        return False
    return db.scalar(
        select(models.Like.id).where(
            models.Like.user_id == viewer.id,
            models.Like.target_type == target_type,
            models.Like.target_id == target_id,
        )
    ) is not None


def _viewer_saved(db: Session, viewer: models.User | None, thread_id: int) -> bool:
    if viewer is None:
        return False
    return db.scalar(
        select(models.Save.id).where(
            models.Save.user_id == viewer.id, models.Save.thread_id == thread_id
        )
    ) is not None


def _comment_count(db: Session, thread_id: int) -> int:
    return db.scalar(
        select(func.count()).select_from(models.Comment).where(models.Comment.thread_id == thread_id)
    ) or 0


def thread_card(db: Session, t: models.Thread, viewer: models.User | None) -> schemas.ThreadCard:
    return schemas.ThreadCard(
        id=t.id,
        title=t.title,
        excerpt=t.excerpt,
        category=t.category,
        cover_image=t.cover_image,
        author=user_out(t.author),
        accent=t.accent,
        badge=t.badge,
        status=t.status,
        date=human_date(t.published_at or t.created_at),
        created_at=t.created_at,
        comment_count=_comment_count(db, t.id) + (t.seed_comments or 0),
        like_count=_like_count(db, "thread", t.id) + (t.seed_likes or 0),
        liked=_viewer_liked(db, viewer, "thread", t.id),
        saved=_viewer_saved(db, viewer, t.id),
    )


def thread_detail(db: Session, t: models.Thread, viewer: models.User | None) -> schemas.ThreadDetail:
    card = thread_card(db, t, viewer)
    return schemas.ThreadDetail(**card.model_dump(), content=t.content or [])


def comment_out(db: Session, c: models.Comment, viewer: models.User | None) -> schemas.CommentOut:
    return schemas.CommentOut(
        id=c.id,
        body=c.body,
        author=user_out(c.author),
        parent_id=c.parent_id,
        created_at=c.created_at,
        time=human_ago(c.created_at),
        like_count=_like_count(db, "comment", c.id) + (c.seed_likes or 0),
        liked=_viewer_liked(db, viewer, "comment", c.id),
        replies=[],
    )


def comment_tree(db: Session, thread_id: int, viewer: models.User | None) -> list[schemas.CommentOut]:
    rows = db.scalars(
        select(models.Comment)
        .where(models.Comment.thread_id == thread_id)
        .order_by(models.Comment.created_at.asc())
    ).all()
    by_id: dict[int, schemas.CommentOut] = {}
    roots: list[schemas.CommentOut] = []
    for c in rows:
        by_id[c.id] = comment_out(db, c, viewer)
    for c in rows:
        node = by_id[c.id]
        if c.parent_id and c.parent_id in by_id:
            by_id[c.parent_id].replies.append(node)
        else:
            roots.append(node)
    # newest top-level first (matches prototype where new comments prepend)
    roots.sort(key=lambda n: n.created_at, reverse=True)
    return roots
