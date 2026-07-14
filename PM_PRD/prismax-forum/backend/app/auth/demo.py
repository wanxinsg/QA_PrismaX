"""Demo auth adapter — a self-contained stub so the app runs and demos without
any external identity provider.

It issues a signed JWT in an HTTP-only cookie after a fake "login" (pick a
preset persona or type any name). This is NOT for production use; in production
select the host-system adapter via AUTH_PROVIDER.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi import Request
from jose import JWTError, jwt

from ..config import settings
from .base import AuthAdapter, Identity

ALGO = "HS256"

# Preset personas shown on the demo login screen. These external_ids line up
# with the seeded authors so "logging in as" them shows their own drafts etc.
PRESET_USERS: list[dict] = [
    {"external_id": "demo:you", "name": "You", "avatar_color": "#8C7355"},
    {"external_id": "demo:thorne", "name": "Dr. Thorne", "avatar_color": "#C08457"},
    {"external_id": "demo:nakamura", "name": "M. Nakamura", "avatar_color": "#6E8B7A"},
    {"external_id": "demo:vance", "name": "Dr. L. Vance", "avatar_color": "#9A7AA0"},
]


def issue_token(identity: Identity) -> str:
    now = datetime.now(timezone.utc)
    claims = {
        "sub": identity.external_id,
        "name": identity.name,
        "email": identity.email,
        "color": identity.avatar_color,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(hours=settings.session_ttl_hours)).timestamp()),
    }
    return jwt.encode(claims, settings.session_secret, algorithm=ALGO)


class DemoAuthAdapter(AuthAdapter):
    name = "demo"
    provides_login_routes = True

    def identify(self, request: Request) -> Identity | None:
        token = request.cookies.get(settings.session_cookie)
        if not token:
            return None
        try:
            claims = jwt.decode(token, settings.session_secret, algorithms=[ALGO])
        except JWTError:
            return None
        sub = claims.get("sub")
        if not sub:
            return None
        return Identity(
            external_id=sub,
            name=claims.get("name") or "Anonymous",
            email=claims.get("email"),
            avatar_color=claims.get("color"),
        )
