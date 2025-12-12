from __future__ import annotations

from typing import Any, Dict, Optional

import requests

from config import TeleOpConfig
from .logger import get_logger


class HttpClient:
    """Lightweight HTTP client for Tele-Op backend tests.

    This client wraps ``requests`` and adds:
    - Base URL resolution from ``TeleOpConfig``
    - Automatic ``Authorization`` header using the configured token
    - Structured logging of request and response details
    """

    def __init__(self, config: TeleOpConfig, logger=None) -> None:
        self.config = config
        self.log = logger or get_logger(__name__)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _build_url(self, path: str) -> str:
        if not path.startswith("/"):
            path = "/" + path
        return f"{self.config.base_url}{path}"

    def _log_request(self, method: str, url: str, **kwargs: Any) -> None:
        self.log.info("HTTP %s %s", method.upper(), url)
        headers = kwargs.get("headers") or {}
        params = kwargs.get("params") or {}
        data = kwargs.get("data")
        json_body = kwargs.get("json")

        self.log.debug("Request headers: %s", headers)
        if params:
            self.log.debug("Request params: %s", params)
        if data is not None:
            self.log.debug("Request data: %s", data)
        if json_body is not None:
            self.log.debug("Request json: %s", json_body)

    def _log_response(self, response: requests.Response) -> None:
        text_preview = response.text
        if len(text_preview) > 1000:
            text_preview = text_preview[:1000] + "...<truncated>"
        self.log.info("Response %s %s", response.status_code, response.reason)
        self.log.debug("Response body: %s", text_preview)

    def _prepare_headers(self, headers: Optional[Dict[str, str]]) -> Dict[str, str]:
        headers = dict(headers or {})
        if self.config.token and "Authorization" not in headers:
            headers["Authorization"] = f"Bearer {self.config.token}"
        return headers

    # ------------------------------------------------------------------
    # Public request interface
    # ------------------------------------------------------------------
    def request(self, method: str, path: str, **kwargs: Any) -> requests.Response:
        """Send an HTTP request with logging and base URL handling."""

        url = self._build_url(path)
        headers = self._prepare_headers(kwargs.pop("headers", None))
        kwargs["headers"] = headers

        self._log_request(method, url, **kwargs)
        response = requests.request(method=method, url=url, **kwargs)
        self._log_response(response)
        return response

    def get(self, path: str, params: Optional[Dict[str, Any]] = None, **kwargs: Any) -> requests.Response:
        return self.request("GET", path, params=params, **kwargs)

    def post(self, path: str, json: Any = None, **kwargs: Any) -> requests.Response:
        return self.request("POST", path, json=json, **kwargs)

    def put(self, path: str, json: Any = None, **kwargs: Any) -> requests.Response:
        return self.request("PUT", path, json=json, **kwargs)

    def delete(self, path: str, **kwargs: Any) -> requests.Response:
        return self.request("DELETE", path, **kwargs)


__all__ = ["HttpClient"]
