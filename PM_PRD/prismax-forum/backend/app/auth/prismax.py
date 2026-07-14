"""PrismaX host-system auth adapter — INTEGRATION SKELETON.

PrismaX already has its own user system. To make the forum use it, you (PrismaX)
only need to make `identify()` below return an Identity for an authenticated
request. Everything else in the forum is unchanged.

The most common integration is a JWT that PrismaX already issues to its logged-in
users. Wire it up by setting these env vars (see app/config.py):

    AUTH_PROVIDER=prismax
    PRISMAX_TOKEN_SOURCE=bearer        # or the name of the cookie carrying the JWT
    PRISMAX_JWT_ALGORITHMS=RS256       # or HS256
    PRISMAX_JWT_PUBLIC_KEY=<PEM>       # for RS256
    PRISMAX_JWT_SECRET=<shared secret> # for HS256
    PRISMAX_JWT_AUDIENCE=<aud>         # optional
    PRISMAX_JWT_ISSUER=<iss>           # optional
    PRISMAX_CLAIM_SUB=sub              # claim holding the stable user id
    PRISMAX_CLAIM_NAME=name
    PRISMAX_CLAIM_EMAIL=email

If PrismaX instead authenticates at a reverse proxy and forwards the user via a
trusted header (e.g. X-Auth-User), replace the body of identify() with a couple
of `request.headers.get(...)` reads — that path needs no JWT config at all. A
commented example is included below.
"""
from __future__ import annotations

from fastapi import Request
from jose import JWTError, jwt

from ..config import settings
from .base import AuthAdapter, Identity


class PrismaxAuthAdapter(AuthAdapter):
    name = "prismax"
    # PrismaX owns login/logout in its own app; the forum exposes none.
    provides_login_routes = False

    def _read_token(self, request: Request) -> str | None:
        source = settings.prismax_token_source
        if source == "bearer":
            header = request.headers.get("authorization", "")
            if header.lower().startswith("bearer "):
                return header[7:].strip()
            return None
        # otherwise `source` is treated as a cookie name
        return request.cookies.get(source)

    def identify(self, request: Request) -> Identity | None:
        # --- Option A: trusted reverse-proxy header (uncomment to use) ---
        # uid = request.headers.get("x-auth-user-id")
        # if not uid:
        #     return None
        # return Identity(
        #     external_id=f"prismax:{uid}",
        #     name=request.headers.get("x-auth-user-name", "PrismaX User"),
        #     email=request.headers.get("x-auth-user-email"),
        # )

        # --- Option B: verify a PrismaX-issued JWT ---
        token = self._read_token(request)
        if not token:
            return None

        key = settings.prismax_jwt_public_key or settings.prismax_jwt_secret
        if not key:
            # Misconfiguration: refuse rather than trust an unverified token.
            return None

        options = {}
        decode_kwargs: dict = {"algorithms": settings.prismax_algorithm_list}
        if settings.prismax_jwt_audience:
            decode_kwargs["audience"] = settings.prismax_jwt_audience
        else:
            options["verify_aud"] = False
        if settings.prismax_jwt_issuer:
            decode_kwargs["issuer"] = settings.prismax_jwt_issuer
        if options:
            decode_kwargs["options"] = options

        try:
            claims = jwt.decode(token, key, **decode_kwargs)
        except JWTError:
            return None

        sub = claims.get(settings.prismax_claim_sub)
        if not sub:
            return None
        return Identity(
            external_id=f"prismax:{sub}",
            name=claims.get(settings.prismax_claim_name) or "PrismaX User",
            email=claims.get(settings.prismax_claim_email),
        )
