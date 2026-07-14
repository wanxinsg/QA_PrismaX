"""Auth adapter factory — selects the adapter from settings.auth_provider."""
from __future__ import annotations

from functools import lru_cache

from ..config import settings
from .base import AuthAdapter, Identity
from .demo import DemoAuthAdapter
from .prismax import PrismaxAuthAdapter

_REGISTRY = {
    "demo": DemoAuthAdapter,
    "prismax": PrismaxAuthAdapter,
}


@lru_cache
def get_adapter() -> AuthAdapter:
    provider = settings.auth_provider.lower()
    adapter_cls = _REGISTRY.get(provider)
    if adapter_cls is None:
        raise RuntimeError(
            f"Unknown AUTH_PROVIDER '{provider}'. Valid options: {', '.join(_REGISTRY)}"
        )
    return adapter_cls()


__all__ = ["AuthAdapter", "Identity", "get_adapter"]
