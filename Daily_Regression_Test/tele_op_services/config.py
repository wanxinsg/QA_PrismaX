from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass
class TeleOpConfig:
    """Configuration for Tele-Op backend regression tests.

    Values are primarily taken from environment variables so that
    the tests can run in different environments without code changes.
    """

    scheme: str = "http"
    host: str = "localhost"
    port: int = 8081
    base_path: str = ""

    robot_id: str = "arm1"
    # 默认使用经过验证的 Tele-Op 队列用户，用于日常回归
    user_id: str = "1073381"
    token: str = "LrwLmEoJ1YHkrdhZFseU_yfOjX9ue3woI_vDBHvaL8M"

    @property
    def base_url(self) -> str:
        base = self.base_path or ""
        if base and not base.startswith("/"):
            base = "/" + base
        return f"{self.scheme}://{self.host}:{self.port}{base}"


def load_config() -> TeleOpConfig:
    """Load configuration from environment variables.

    TELE_SCHEME: http / https (default: http)
    TELE_HOST: backend host (default: localhost)
    TELE_PORT: backend port (default: 8081)
    TELE_BASE: optional base path prefix for the API

    ROBOT_ID: robot identifier used in test expectations
    USER_ID: user id used for authorization / ownership checks
    TOKEN: bearer token for Authorization header
    """

    scheme = os.getenv("TELE_SCHEME", "http")
    host = os.getenv("TELE_HOST", "localhost")
    port = int(os.getenv("TELE_PORT", "8081"))
    base_path = os.getenv("TELE_BASE", "")

    robot_id = os.getenv("ROBOT_ID", "arm1")
    # 如未显式指定，则回落到默认回归账号 1073381
    user_id = os.getenv("USER_ID", "1073381")
    token = os.getenv("TOKEN", "LrwLmEoJ1YHkrdhZFseU_yfOjX9ue3woI_vDBHvaL8M")

    return TeleOpConfig(
        scheme=scheme,
        host=host,
        port=port,
        base_path=base_path,
        robot_id=robot_id,
        user_id=user_id,
        token=token,
    )


__all__ = ["TeleOpConfig", "load_config"]
