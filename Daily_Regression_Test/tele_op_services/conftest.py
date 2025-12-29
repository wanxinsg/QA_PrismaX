import json
import time
from typing import Any, Dict, List

import pytest
import socketio
import allure

from case_util.http_request import HttpClient
from case_util.logger import get_logger
from config import load_config


@pytest.fixture(scope="session")
def config():
    """Session-wide Tele-Op test configuration."""

    return load_config()


@pytest.fixture(scope="session")
def logger():
    """Shared logger instance for tests."""

    return get_logger("tele_op_tests")


@pytest.fixture(scope="session")
def api_client(config, logger):
    """HTTP client bound to the Tele-Op backend under test."""

    return HttpClient(config=config, logger=logger)


# ---- Socket.IO test fixtures (for queue_update_event tests) ------------------


@pytest.fixture(scope="session")
def env_config(config):
    """Alias Tele-Op HTTP config as env_config for socket tests."""

    return config


class QueueEventCollector:
    def __init__(self) -> None:
        self.events: List[Dict[str, Any]] = []

    def push(self, data: Dict[str, Any]) -> None:
        self.events.append(data)

    def wait_first(self, timeout: float = 10.0) -> Dict[str, Any]:
        deadline = time.time() + timeout
        while time.time() < deadline:
            if self.events:
                return self.events[0]
            time.sleep(0.05)
        raise TimeoutError("Timed out waiting for first queue_update event")


@pytest.fixture(scope="function")
def socketio_client(env_config, logger):
    """
    Connect to Socket.IO of tele-op backend and yield (client, collector).
    Requires USER_ID and TOKEN to be valid for the backend DB.
    """

    if not env_config.user_id or not env_config.token:
        pytest.skip("USER_ID and TOKEN must be provided via env vars to run Socket.IO tests")

    server_url = env_config.base_url
    collector = QueueEventCollector()
    sio = socketio.Client(
        reconnection=True,
        reconnection_attempts=0,
        logger=False,
        engineio_logger=False,
    )

    @sio.event
    def connect():
        logger.info("Connected sid=%s", getattr(sio, "sid", None))

    @sio.event
    def disconnect():
        logger.info("Disconnected from server")

    @sio.event
    def connect_error(data):
        try:
            pretty = json.dumps(data, ensure_ascii=False)
        except Exception:
            pretty = str(data)
        logger.error("connect_error: %s", pretty)
        # 将连接错误作为事件推入 collector，便于上层逻辑进行 skip 处理
        collector.push({"_type": "connect_error", "payload": data})

    @sio.on("connection_success")
    def on_connection_success(msg):
        try:
            pretty = json.dumps(msg, ensure_ascii=False)
        except Exception:
            pretty = str(msg)
        logger.info("connection_success: %s", pretty)
        collector.push({"_type": "connection_success", "payload": msg})

    @sio.on("queue_update")
    def on_queue_update(data):
        try:
            pretty = json.dumps(data, ensure_ascii=False)
        except Exception:
            pretty = str(data)
        logger.info("queue_update: %s", pretty)
        collector.push({"_type": "queue_update", "payload": data})

    try:
        sio.connect(
            server_url,
            auth={
                "robotId": env_config.robot_id,
                "token": env_config.token,
                "userId": env_config.user_id,
            },
            wait=False,
        )
    except Exception as e:
        try:
            pretty = json.dumps({"error": str(e)}, ensure_ascii=False)
        except Exception:
            pretty = str(e)
        logger.error("connect_error (exception): %s", pretty)
        pytest.skip(f"backend not reachable: {pretty}")

    try:
        yield sio, collector
    finally:
        try:
            sio.disconnect()
        except Exception:
            pass

