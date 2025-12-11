import os
import sys

# Ensure this directory is importable when running pytest from project root
_THIS_DIR = os.path.dirname(__file__)
if _THIS_DIR not in sys.path:
    sys.path.insert(0, _THIS_DIR)

import json
import time
from typing import Any, Dict, List

import pytest
import socketio
import allure
from socketio import exceptions as sio_exceptions

from case_util.logger import get_logger
from case_util.http_request import build_http_client_from_env, HttpClient
from config import EnvConfig


logger = get_logger(__name__)


@pytest.fixture(scope="session")
def env_config() -> EnvConfig:
    cfg = EnvConfig()
    logger.info("Using Tele-Op backend: %s", cfg.base_url)
    return cfg


@pytest.fixture(scope="session")
def http_client(env_config: EnvConfig) -> HttpClient:
    return build_http_client_from_env(env_prefix="TELE")


@pytest.fixture(autouse=True)
def annotate_robot(env_config: EnvConfig, request):
    """
    Annotate every test with the current robot id so Allure can show
    arm1/arm2 distinctly. Also append robot id to the test title.
    """
    robot = getattr(env_config, "robot_id", "unknown")
    try:
        allure.dynamic.parameter("robot", robot)
        original = getattr(request, "node", None)
        title = getattr(original, "name", None) or "test"
        allure.dynamic.title(f"{title} [{robot}]")
    except Exception:
        # Non-fatal if Allure dynamic update fails
        pass

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
def socketio_client(env_config: EnvConfig):
    """
    Connect to Socket.IO of tele-op backend and yield (client, collector).
    Requires USER_ID and TOKEN to be valid for the backend DB.
    """
    if not env_config.user_id or not env_config.token:
        pytest.skip("USER_ID and TOKEN must be provided via env vars to run Socket.IO tests")

    server_url = env_config.base_url
    collector = QueueEventCollector()
    sio = socketio.Client(reconnection=True, reconnection_attempts=0, logger=False, engineio_logger=False)

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
            auth={"robotId": env_config.robot_id, "token": env_config.token, "userId": env_config.user_id},
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


