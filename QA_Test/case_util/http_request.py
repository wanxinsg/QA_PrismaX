import json
import logging
import os
from typing import Any, Dict, Optional, Tuple, Union

import requests

from .logger import get_logger

logger = get_logger(__name__)


class HttpClient:
    def __init__(
        self,
        base_url: str,
        default_headers: Optional[Dict[str, str]] = None,
        timeout: int = 10,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.default_headers = default_headers or {}
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update(self.default_headers)
        logger.debug("HttpClient initialized base_url=%s", self.base_url)

    def _make_url(self, path: str) -> str:
        if path.startswith("http://") or path.startswith("https://"):
            return path
        return f"{self.base_url}/{path.lstrip('/')}"

    def set_header(self, key: str, value: Optional[str]) -> None:
        if value is None:
            self.session.headers.pop(key, None)
        else:
            self.session.headers[key] = value

    def get(
        self,
        path: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        timeout: Optional[int] = None,
    ) -> requests.Response:
        url = self._make_url(path)
        hdrs = {**self.session.headers, **(headers or {})}
        logger.info("GET %s params=%s", url, params)
        resp = self.session.get(url, params=params, headers=hdrs, timeout=timeout or self.timeout)
        logger.debug("Response %s %s", resp.status_code, resp.text[:500])
        return resp

    def post_json(
        self,
        path: str,
        json_body: Union[Dict[str, Any], list, None] = None,
        headers: Optional[Dict[str, str]] = None,
        timeout: Optional[int] = None,
    ) -> requests.Response:
        url = self._make_url(path)
        hdrs = {"Content-Type": "application/json", **self.session.headers, **(headers or {})}
        payload_str = json.dumps(json_body, ensure_ascii=False) if json_body is not None else None
        logger.info("POST %s json=%s", url, payload_str)
        resp = self.session.post(url, json=json_body, headers=hdrs, timeout=timeout or self.timeout)
        logger.debug("Response %s %s", resp.status_code, resp.text[:500])
        return resp


def build_http_client_from_env(env_prefix: str = "TELE") -> HttpClient:
    """
    Build HttpClient using environment:
      {PREFIX}_HOST, {PREFIX}_PORT, {PREFIX}_BASE (optional), {PREFIX}_SCHEME (default http)
    """
    scheme = os.getenv(f"{env_prefix}_SCHEME", "http")
    host = os.getenv(f"{env_prefix}_HOST", "localhost")
    port = os.getenv(f"{env_prefix}_PORT", "8081")
    base = os.getenv(f"{env_prefix}_BASE", "").strip("/")
    base_url = f"{scheme}://{host}:{port}"
    if base:
        base_url = f"{base_url}/{base}"
    return HttpClient(base_url=base_url)


