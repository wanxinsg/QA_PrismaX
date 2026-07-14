"""Category route — derived from published threads."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .. import schemas
from ..db import get_db
from ..models import Thread

router = APIRouter(prefix="/api", tags=["categories"])


@router.get("/categories", response_model=list[schemas.CategoryOut])
def list_categories(db: Session = Depends(get_db)):
    rows = db.execute(
        select(Thread.category, func.count(Thread.id))
        .where(Thread.status == "published")
        .group_by(Thread.category)
        .order_by(func.count(Thread.id).desc())
    ).all()
    total = sum(c for _, c in rows)
    out = [schemas.CategoryOut(label="All", count=total)]
    out += [schemas.CategoryOut(label=label, count=count) for label, count in rows]
    return out
