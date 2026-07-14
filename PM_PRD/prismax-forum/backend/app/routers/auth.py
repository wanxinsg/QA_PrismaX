"""Auth routes.

`GET /me` and `POST /logout` are provider-agnostic. The demo-only login routes
are registered solely when the active adapter advertises `provides_login_routes`,
so swapping in the PrismaX adapter automatically drops the stub login.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session

from .. import schemas, serializers
from ..auth import get_adapter
from ..auth.deps import current_user, optional_user
from ..auth.demo import PRESET_USERS, DemoAuthAdapter, issue_token
from ..auth.base import Identity
from ..config import settings
from ..db import get_db
from ..models import User

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.get("/me", response_model=schemas.UserOut | None)
def me(user: User | None = Depends(optional_user)):
    return serializers.user_out(user) if user else None


@router.get("/provider")
def provider():
    adapter = get_adapter()
    return {"provider": adapter.name, "login_routes": adapter.provides_login_routes}


@router.post("/logout", response_model=schemas.Message)
def logout(response: Response):
    response.delete_cookie(settings.session_cookie, path="/")
    return schemas.Message(detail="Logged out.")


# ---- demo-only login routes ----
def _require_demo() -> DemoAuthAdapter:
    adapter = get_adapter()
    if not isinstance(adapter, DemoAuthAdapter):
        raise HTTPException(status_code=404, detail="Demo login is disabled.")
    return adapter


@router.get("/demo/users")
def demo_users(_: DemoAuthAdapter = Depends(_require_demo)):
    return PRESET_USERS


@router.post("/demo/login", response_model=schemas.UserOut)
def demo_login(
    payload: schemas.DemoLoginIn,
    response: Response,
    db: Session = Depends(get_db),
    _: DemoAuthAdapter = Depends(_require_demo),
):
    if payload.external_id:
        preset = next((u for u in PRESET_USERS if u["external_id"] == payload.external_id), None)
        if preset is None:
            raise HTTPException(status_code=400, detail="Unknown preset user.")
        identity = Identity(
            external_id=preset["external_id"],
            name=preset["name"],
            avatar_color=preset.get("avatar_color"),
        )
    elif payload.name and payload.name.strip():
        name = payload.name.strip()
        slug = "demo:" + "".join(ch.lower() if ch.isalnum() else "-" for ch in name).strip("-")
        identity = Identity(external_id=slug, name=name, avatar_color="#8C7355")
    else:
        raise HTTPException(status_code=400, detail="Provide a preset external_id or a name.")

    from ..auth.deps import _upsert_user

    user = _upsert_user(db, identity)
    token = issue_token(identity)
    response.set_cookie(
        settings.session_cookie,
        token,
        max_age=settings.session_ttl_hours * 3600,
        httponly=True,
        samesite="lax",
        path="/",
    )
    return serializers.user_out(user)
