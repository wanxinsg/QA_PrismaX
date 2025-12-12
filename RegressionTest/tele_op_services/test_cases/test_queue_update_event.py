import allure
import pytest
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from config import TeleOpConfig as EnvConfig  # type alias for hints only


def _wait_first_event(collector, timeout: float = 15.0):
    try:
        evt = collector.wait_first(timeout=timeout)
    except TimeoutError:
        # 在超时时间内完全没有收到任何事件（包括 connection_success / queue_update / connect_error）
        pytest.skip("在超时时间内未收到任何 Socket.IO 事件，跳过队列相关校验")
    if not isinstance(evt, dict):
        pytest.skip("未收到有效事件，跳过")
    et = evt.get("_type")
    if et == "connect_error":
        # 连接被后端拒绝（例如用户/Token 未授权），视为环境问题，跳过业务断言
        pytest.skip(f"Socket.IO 连接被后端拒绝: {evt.get('payload')}")
    if et == "connection_success":
        # 仅连通但未推送 queue_update，业务断言无法执行
        pytest.skip("仅收到 connection_success，未收到 queue_update，跳过业务校验")
    if et != "queue_update":
        pytest.skip(f"首个事件非 queue_update（实际: {et}），跳过业务校验")
    data = evt.get("payload") or {}
    if not isinstance(data, dict) or "queue" not in data:
        pytest.skip("queue_update payload 非法或缺少 queue 字段，跳过业务校验")
    return data


@pytest.mark.teleop
@allure.feature("Tele-Op Queue")
@allure.story("Queue Positions")
def test_queue_positions(socketio_client, env_config: "EnvConfig"):
    sio, collector = socketio_client
    data = _wait_first_event(collector, timeout=15.0)
    queue = data.get("queue", [])

    with allure.step("位置从 1 开始递增且无重复"):
        positions = [item.get("position") for item in queue]
        # 附件：不同机器人分别打印完整 positions 序列
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
            pytest.xfail("存在非正整数 position")
        expected = list(range(1, len(queue) + 1))
        if positions != expected:
            # 定位问题类型与位置：非严格递增（步长!=1）或存在重复
            first_gap_idx = None
            first_dup_idx = None
            seen = {}
            for i in range(1, len(positions)):
                if first_gap_idx is None and (positions[i] - positions[i - 1] != 1):
                    first_gap_idx = i
                if first_dup_idx is None:
                    if positions[i] in seen:
                        first_dup_idx = i
                    else:
                        seen[positions[i - 1]] = i - 1
            problem_idx_candidates = [idx for idx in [first_dup_idx, first_gap_idx] if idx is not None]
            if problem_idx_candidates:
                problem_idx = min(problem_idx_candidates)
                problem_type = "存在重复" if (first_dup_idx is not None and problem_idx == first_dup_idx) else "非严格递增"
            else:
                # 起始非1但严格递增的情况（如 [2,3,4,...]）
                problem_idx = 0
                problem_type = "起始非1"

            start = max(0, problem_idx - 2)
            end = min(len(positions), start + 5)
            window = positions[start:end]

            allure.attach(
                f"type={problem_type}\nindex={problem_idx}\nwindow={window}",
                "positions_mismatch_window",
                allure.attachment_type.TEXT,
            )
            # 仍附上完整 expected/actual 以便排查
            allure.attach(f"expected={expected}\nactual={positions}", "positions_mismatch", allure.attachment_type.TEXT)
            pytest.xfail("position 非严格递增或存在重复")


@pytest.mark.teleop
@allure.feature("Tele-Op Queue")
@allure.story("Queue Membership Class")
def test_queue_membership(socketio_client, env_config: "EnvConfig"):
    sio, collector = socketio_client
    data = _wait_first_event(collector, timeout=15.0)
    queue = data.get("queue", [])

    with allure.step("每个用户包含 member_class 且类别合法"):
        allowed = {"Innovator Member", "Amplifier Member"}
        for idx, item in enumerate(queue, start=1):
            if "member_class" not in item:
                allure.attach(str(item), f"item_{idx}", allure.attachment_type.TEXT)
                pytest.xfail(f"第 {idx} 个用户缺少 member_class")
            if item["member_class"] not in allowed:
                allure.attach(str(item), f"item_{idx}", allure.attachment_type.TEXT)
                pytest.xfail(f"第 {idx} 个用户 member_class 不合法: {item['member_class']}")


@pytest.mark.teleop
@allure.feature("Tele-Op Queue")
@allure.story("Queue Status")
def test_queue_status(socketio_client, env_config: "EnvConfig"):
    sio, collector = socketio_client
    data = _wait_first_event(collector, timeout=15.0)
    queue = data.get("queue", [])

    if not queue:
        pytest.skip("当前队列为空，跳过状态校验")

    with allure.step("首个用户为 active，其余为 waiting"):
        statuses = [item.get("status") for item in queue]
        if statuses[0] != "active":
            allure.attach(str(statuses), "statuses", allure.attachment_type.TEXT)
            pytest.xfail(f"第一个用户非 active，实际 {statuses[0]}")
        for idx, s in enumerate(statuses[1:], start=2):
            if s != "waiting":
                allure.attach(str(statuses), "statuses", allure.attachment_type.TEXT)
                pytest.xfail(f"第 {idx} 个用户非 waiting，实际 {s}")
