"""Thread routes: browse, read, author, like, save."""
from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from .. import models, schemas, serializers
from ..auth.deps import current_user, optional_user
from ..db import get_db
from ..models import Comment, Like, Save, Thread, User

router = APIRouter(prefix="/api", tags=["threads"])


def _get_thread(db: Session, thread_id: int) -> Thread:
    t = db.get(Thread, thread_id)
    if t is None:
        raise HTTPException(status_code=404, detail="Thread not found.")
    return t


@router.get("/threads", response_model=schemas.ThreadList)
def list_threads(
    db: Session = Depends(get_db),
    viewer: User | None = Depends(optional_user),
    category: str = Query("All"),
    sort: str = Query("latest", pattern="^(latest|discussed)$"),
    q: str | None = Query(None),
    limit: int = Query(12, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    stmt = select(Thread).where(Thread.status == "published")
    if category and category != "All":
        stmt = stmt.where(Thread.category == category)
    if q:
        like = f"%{q.strip()}%"
        stmt = stmt.where(or_(Thread.title.ilike(like), Thread.excerpt.ilike(like)))

    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0

    if sort == "discussed":
        comment_count = (
            select(func.count(Comment.id))
            .where(Comment.thread_id == Thread.id)
            .scalar_subquery()
        )
        stmt = stmt.order_by(comment_count.desc(), Thread.created_at.desc())
    else:
        stmt = stmt.order_by(
            func.coalesce(Thread.published_at, Thread.created_at).desc(), Thread.id.desc()
        )

    rows = db.scalars(stmt.limit(limit).offset(offset)).all()
    items = [serializers.thread_card(db, t, viewer) for t in rows]
    return schemas.ThreadList(items=items, total=total)


@router.get("/me/drafts", response_model=list[schemas.ThreadCard])
def my_drafts(db: Session = Depends(get_db), user: User = Depends(current_user)):
    rows = db.scalars(
        select(Thread)
        .where(Thread.author_id == user.id, Thread.status == "draft")
        .order_by(Thread.updated_at.desc())
    ).all()
    return [serializers.thread_card(db, t, user) for t in rows]


@router.get("/me/saved", response_model=list[schemas.ThreadCard])
def my_saved(db: Session = Depends(get_db), user: User = Depends(current_user)):
    rows = db.scalars(
        select(Thread)
        .join(Save, Save.thread_id == Thread.id)
        .where(Save.user_id == user.id, Thread.status == "published")
        .order_by(Save.created_at.desc())
    ).all()
    return [serializers.thread_card(db, t, user) for t in rows]


@router.get("/threads/{thread_id}", response_model=schemas.ThreadDetail)
def get_thread(
    thread_id: int,
    db: Session = Depends(get_db),
    viewer: User | None = Depends(optional_user),
):
    t = _get_thread(db, thread_id)
    # Drafts are only visible to their author.
    if t.status == "draft" and (viewer is None or viewer.id != t.author_id):
        raise HTTPException(status_code=404, detail="Thread not found.")
    return serializers.thread_detail(db, t, viewer)


def _excerpt_from(payload: schemas.ThreadCreate | schemas.ThreadUpdate) -> str:
    if payload.excerpt:
        return payload.excerpt[:200]
    for b in payload.content or []:
        if b.text and b.text.strip():
            return b.text.strip()[:200]
    return "A new monograph awaiting peer review."


@router.post("/threads", response_model=schemas.ThreadDetail, status_code=201)
def create_thread(
    payload: schemas.ThreadCreate,
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
):
    now = datetime.now(timezone.utc)
    t = Thread(
        author_id=user.id,
        title=payload.title.strip(),
        category=payload.category or "Discourse",
        excerpt=_excerpt_from(payload),
        cover_image=payload.cover_image,
        content=[b.model_dump() for b in payload.content],
        status=payload.status,
        published_at=now if payload.status == "published" else None,
    )
    db.add(t)
    db.commit()
    db.refresh(t)
    return serializers.thread_detail(db, t, user)


@router.patch("/threads/{thread_id}", response_model=schemas.ThreadDetail)
def update_thread(
    thread_id: int,
    payload: schemas.ThreadUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
):
    t = _get_thread(db, thread_id)
    if t.author_id != user.id:
        raise HTTPException(status_code=403, detail="Not your thread.")

    data = payload.model_dump(exclude_unset=True)
    if "content" in data and data["content"] is not None:
        t.content = [b.model_dump() if hasattr(b, "model_dump") else b for b in payload.content]
    for field in ("title", "category", "cover_image"):
        if field in data and data[field] is not None:
            setattr(t, field, data[field])
    if "excerpt" in data:
        t.excerpt = data["excerpt"] or _excerpt_from(payload)
    if "status" in data and data["status"]:
        if data["status"] == "published" and t.status != "published":
            t.published_at = datetime.now(timezone.utc)
        t.status = data["status"]

    db.commit()
    db.refresh(t)
    return serializers.thread_detail(db, t, user)


@router.post("/threads/{thread_id}/publish", response_model=schemas.ThreadDetail)
def publish_thread(
    thread_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
):
    t = _get_thread(db, thread_id)
    if t.author_id != user.id:
        raise HTTPException(status_code=403, detail="Not your thread.")
    if t.status != "published":
        t.status = "published"
        t.published_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(t)
    return serializers.thread_detail(db, t, user)


@router.delete("/threads/{thread_id}", response_model=schemas.Message)
def delete_thread(
    thread_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
):
    t = _get_thread(db, thread_id)
    if t.author_id != user.id:
        raise HTTPException(status_code=403, detail="Not your thread.")
    db.delete(t)
    db.commit()
    return schemas.Message(detail="Thread deleted.")


# ---------- likes / saves ----------
def _toggle_like(db: Session, user: User, target_type: str, target_id: int) -> schemas.ToggleResult:
    existing = db.scalar(
        select(Like).where(
            Like.user_id == user.id,
            Like.target_type == target_type,
            Like.target_id == target_id,
        )
    )
    if existing:
        db.delete(existing)
        active = False
    else:
        db.add(Like(user_id=user.id, target_type=target_type, target_id=target_id))
        active = True
    db.commit()
    count = serializers._like_count(db, target_type, target_id)
    # Include the imported baseline so the UI count stays consistent with cards.
    if target_type == "thread":
        t = db.get(Thread, target_id)
        count += (t.seed_likes or 0) if t else 0
    elif target_type == "comment":
        c = db.get(Comment, target_id)
        count += (c.seed_likes or 0) if c else 0
    return schemas.ToggleResult(active=active, count=count)


@router.post("/threads/{thread_id}/like", response_model=schemas.ToggleResult)
def toggle_thread_like(
    thread_id: int, db: Session = Depends(get_db), user: User = Depends(current_user)
):
    _get_thread(db, thread_id)
    return _toggle_like(db, user, "thread", thread_id)


@router.post("/threads/{thread_id}/save", response_model=schemas.ToggleResult)
def toggle_thread_save(
    thread_id: int, db: Session = Depends(get_db), user: User = Depends(current_user)
):
    _get_thread(db, thread_id)
    existing = db.scalar(
        select(Save).where(Save.user_id == user.id, Save.thread_id == thread_id)
    )
    if existing:
        db.delete(existing)
        active = False
    else:
        db.add(Save(user_id=user.id, thread_id=thread_id))
        active = True
    db.commit()
    return schemas.ToggleResult(active=active, count=0)
