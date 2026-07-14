"""Comment routes (nested one level: comments + replies)."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import schemas, serializers
from ..auth.deps import current_user, optional_user
from ..db import get_db
from ..models import Comment, Like, Thread, User
from .threads import _toggle_like

router = APIRouter(prefix="/api", tags=["comments"])


@router.get("/threads/{thread_id}/comments", response_model=list[schemas.CommentOut])
def list_comments(
    thread_id: int,
    db: Session = Depends(get_db),
    viewer: User | None = Depends(optional_user),
):
    if db.get(Thread, thread_id) is None:
        raise HTTPException(status_code=404, detail="Thread not found.")
    return serializers.comment_tree(db, thread_id, viewer)


@router.post("/threads/{thread_id}/comments", response_model=schemas.CommentOut, status_code=201)
def create_comment(
    thread_id: int,
    payload: schemas.CommentCreate,
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
):
    if db.get(Thread, thread_id) is None:
        raise HTTPException(status_code=404, detail="Thread not found.")
    if payload.parent_id is not None:
        parent = db.get(Comment, payload.parent_id)
        if parent is None or parent.thread_id != thread_id:
            raise HTTPException(status_code=400, detail="Invalid parent comment.")
        # keep nesting to one level: a reply's parent is always a top-level comment
        if parent.parent_id is not None:
            payload.parent_id = parent.parent_id

    c = Comment(
        thread_id=thread_id,
        author_id=user.id,
        parent_id=payload.parent_id,
        body=payload.body.strip(),
    )
    db.add(c)
    db.commit()
    db.refresh(c)
    return serializers.comment_out(db, c, user)


@router.post("/comments/{comment_id}/like", response_model=schemas.ToggleResult)
def toggle_comment_like(
    comment_id: int, db: Session = Depends(get_db), user: User = Depends(current_user)
):
    if db.get(Comment, comment_id) is None:
        raise HTTPException(status_code=404, detail="Comment not found.")
    return _toggle_like(db, user, "comment", comment_id)
