"""Auth adapter contract.

The forum core never talks to a concrete identity provider. It depends only on
this interface. To plug the forum into another user system (e.g. PrismaX's),
implement a new AuthAdapter and select it via the AUTH_PROVIDER env var — no
other backend code changes.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

from fastapi import Request


@dataclass
class Identity:
    """A provider-agnostic view of the signed-in user.

    `external_id` must be stable for a given person across logins — it is what
    we key our local `users` row on.
    """

    external_id: str
    name: str
    email: str | None = None
    avatar_color: str | None = None


class AuthAdapter(ABC):
    """Resolves the current user from an incoming request."""

    #: short identifier, e.g. "demo" or "prismax"
    name: str = "base"

    #: True if this adapter exposes its own login/logout HTTP routes
    #: (the demo adapter does; a host-system adapter typically does not).
    provides_login_routes: bool = False

    @abstractmethod
    def identify(self, request: Request) -> Identity | None:
        """Return the Identity for this request, or None if not authenticated."""
        raise NotImplementedError
