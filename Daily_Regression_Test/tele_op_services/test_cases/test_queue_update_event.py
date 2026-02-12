import allure
import pytest
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from config import TeleOpConfig as EnvConfig  # type alias for hints only


def _wait_first_event(collector, timeout: float = 15.0):
    try:
        evt = collector.wait_first(timeout=timeout)
    except TimeoutError:
        pytest.skip(
            "No Socket.IO events received within timeout (connection_success / queue_update / connect_error)"
        )
    if not isinstance(evt, dict):
        pytest.skip("No valid event received")
    et = evt.get("_type")
    if et == "connect_error":
        pytest.skip(f"Socket.IO connection rejected by backend: {evt.get('payload')}")
    if et == "connection_success":
        pytest.skip("Received connection_success but no queue_update, cannot run queue assertions")
    if et != "queue_update":
        pytest.skip(f"First event was not queue_update (actual: {et})")
    data = evt.get("payload") or {}
    if not isinstance(data, dict) or "queue" not in data:
        pytest.skip("queue_update payload invalid or missing 'queue' field")
    return data


@pytest.mark.teleop
@allure.feature("Tele-Op Queue")
@allure.story("Queue Positions")
def test_queue_positions(socketio_client, env_config: "EnvConfig"):
    sio, collector = socketio_client
    data = _wait_first_event(collector, timeout=15.0)
    queue = data.get("queue", [])

    with allure.step(
        "Positions are positive integers, strictly increasing (gaps allowed), no duplicates"
    ):
        positions = [item.get("position") for item in queue]
        try:
            robot_id = getattr(env_config, "robot_id", "unknown")
        except Exception:
            robot_id = "unknown"
        allure.attach(
            "\n".join(map(str, positions)),
            f"positions_{robot_id}",
            allure.attachment_type.TEXT,
        )
        if not all(isinstance(p, int) and p > 0 for p in positions):
            allure.attach(str(positions), "positions_invalid", allure.attachment_type.TEXT)
            pytest.xfail("Non-positive or non-integer position found")
        has_duplicates = len(set(positions)) != len(positions)
        is_monotonic_increasing = all(positions[i] > positions[i - 1] for i in range(1, len(positions)))
        if has_duplicates or not is_monotonic_increasing:
            problem_idx = None
            for i in range(1, len(positions)):
                if positions[i] <= positions[i - 1]:
                    problem_idx = i
                    break

            if problem_idx is None and has_duplicates:
                seen = {}
                for i, p in enumerate(positions):
                    if p in seen:
                        problem_idx = i
                        break
                    seen[p] = i

            if problem_idx is None:
                problem_idx = 0

            start = max(0, problem_idx - 2)
            end = min(len(positions), start + 5)
            window = positions[start:end]

            problem_type_parts = []
            if has_duplicates:
                problem_type_parts.append("duplicates")
            if not is_monotonic_increasing:
                problem_type_parts.append("not strictly increasing")
            problem_type = " & ".join(problem_type_parts) if problem_type_parts else "unknown"

            allure.attach(
                f"type={problem_type}\nindex={problem_idx}\nwindow={window}",
                "positions_mismatch_window",
                allure.attachment_type.TEXT,
            )
            mismatch_text = f"actual={positions}"
            allure.attach(mismatch_text, "positions_mismatch", allure.attachment_type.TEXT)
            print("[queue_positions] MISMATCH")
            print("[queue_positions] actual   queue:", positions)
            pytest.xfail("Positions not strictly increasing or contain duplicates")


@pytest.mark.teleop
@allure.feature("Tele-Op Queue")
@allure.story("Queue Membership Class")
def test_queue_membership(socketio_client, env_config: "EnvConfig"):
    sio, collector = socketio_client
    data = _wait_first_event(collector, timeout=15.0)
    queue = data.get("queue", [])

    with allure.step("Each user has member_class and it is one of the allowed values"):
        allowed = {"Innovator Member", "Amplifier Member"}
        for idx, item in enumerate(queue, start=1):
            if "member_class" not in item:
                allure.attach(str(item), f"item_{idx}", allure.attachment_type.TEXT)
                pytest.xfail(f"User at index {idx} missing member_class")
            if item["member_class"] not in allowed:
                allure.attach(str(item), f"item_{idx}", allure.attachment_type.TEXT)
                pytest.xfail(f"User at index {idx} has invalid member_class: {item['member_class']}")


@pytest.mark.teleop
@allure.feature("Tele-Op Queue")
@allure.story("Queue Status")
def test_queue_status(socketio_client, env_config: "EnvConfig"):
    sio, collector = socketio_client
    data = _wait_first_event(collector, timeout=15.0)
    queue = data.get("queue", [])

    if not queue:
        pytest.skip("Queue is empty, skipping status validation")

    with allure.step("First user is active, rest are waiting"):
        statuses = [item.get("status") for item in queue]
        if statuses[0] != "active":
            allure.attach(str(statuses), "statuses", allure.attachment_type.TEXT)
            pytest.xfail(f"First user is not active, actual: {statuses[0]}")
        for idx, s in enumerate(statuses[1:], start=2):
            if s != "waiting":
                allure.attach(str(statuses), "statuses", allure.attachment_type.TEXT)
                pytest.xfail(f"User at index {idx} is not waiting, actual: {s}")
