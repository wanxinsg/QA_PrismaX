"""FastAPI dependencies for resolving the current user.

This is the single seam between the forum and whatever identity provider is
configured. Routers depend on `current_user` / `optional_user`; they never know
which adapter produced the identity.
"""
from __future__ import annotations

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import User
from . import Identity, get_adapter


def _upsert_user(db: Session, identity: Identity) -> User:
    user = db.scalar(select(User).where(User.external_id == identity.external_id))
    if user is None:
        user = User(
            external_id=identity.external_id,
            name=identity.name,
            email=identity.email,
            avatar_color=identity.avatar_color,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    else:
        # keep profile fields fresh from the provider
        changed = False
        if user.name != identity.name and identity.name:
            user.name = identity.name
            changed = True
        if identity.email and user.email != identity.email:
            user.email = identity.email
            changed = True
        if changed:
            db.commit()
            db.refresh(user)
    return user


def optional_user(request: Request, db: Session = Depends(get_db)) -> User | None:
    identity = get_adapter().identify(request)
    if identity is None:
        return None
    return _upsert_user(db, identity)


def current_user(user: User | None = Depends(optional_user)) -> User:
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required.",
        )
    return user
