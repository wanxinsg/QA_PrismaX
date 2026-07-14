"""Application configuration, loaded from environment / .env."""
from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # --- general ---
    app_name: str = "Prisma(x) Forum API"
    database_url: str = "sqlite:///./forum.db"

    # Comma-separated list of allowed CORS origins (the frontend).
    cors_origins: str = "http://localhost:3001,http://127.0.0.1:3001,http://34.186.168.140:3001"

    # --- auth ---
    # Which auth adapter to use: "demo" (built-in stub) or "prismax" (host system).
    auth_provider: str = "demo"
    # Name of the cookie that carries the session for the demo adapter.
    session_cookie: str = "forum_session"
    # Secret used to sign demo-adapter JWTs. OVERRIDE in production via env.
    session_secret: str = "dev-only-change-me-in-production"
    session_ttl_hours: int = 24 * 14

    # --- prismax adapter (only used when auth_provider == "prismax") ---
    # How PrismaX hands us the user identity. See app/auth/prismax.py.
    # JWT verification material (fill in when integrating):
    prismax_jwt_secret: str = ""          # for HS256 shared-secret tokens
    prismax_jwt_public_key: str = ""      # for RS256 (PEM), takes precedence if set
    prismax_jwt_algorithms: str = "HS256"
    prismax_jwt_audience: str = ""
    prismax_jwt_issuer: str = ""
    # Where to read the token from: "bearer" (Authorization header) or a cookie name.
    prismax_token_source: str = "bearer"
    # JWT claim names to map onto our user identity.
    prismax_claim_sub: str = "sub"
    prismax_claim_name: str = "name"
    prismax_claim_email: str = "email"

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def prismax_algorithm_list(self) -> list[str]:
        return [a.strip() for a in self.prismax_jwt_algorithms.split(",") if a.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
