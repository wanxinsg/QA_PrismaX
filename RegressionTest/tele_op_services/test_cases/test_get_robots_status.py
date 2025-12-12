import pytest
import allure


def _fetch_robots(api_client):
    """Common helper to call GET /robots/status and return robots list."""

    with allure.step("Send GET /robots/status"):
        response = api_client.get("/robots/status")

    with allure.step("Validate HTTP status code is 200"):
        assert response.status_code == 200

    data = response.json()
    assert "robots" in data, "Response must contain 'robots' key"
    assert isinstance(data["robots"], list)
    assert data["robots"], "Robots list should not be empty"
    return data["robots"]


@allure.feature("Tele-Op")
@allure.story("Robots status")
@allure.title("test_get_robots_status_code")
@pytest.mark.regression
@pytest.mark.api
def test_get_robots_status_code(api_client, config):
    """仅校验接口返回 200 且包含配置中的机器人 ID。"""

    robots = _fetch_robots(api_client)

    with allure.step("Validate configured robot exists and has basic fields"):
        robot = next((r for r in robots if r.get("robot_id") == config.robot_id), None)
        assert robot is not None, f"Robot {config.robot_id} not found in response"
        assert isinstance(robot.get("is_available"), bool)
        assert isinstance(robot.get("queue_length"), int)
        assert "youtube_stream_id" in robot
        assert isinstance(robot.get("live_paused"), bool)


@allure.feature("Tele-Op")
@allure.story("Robots status")
@allure.title("test_get_robots_id_list")
@pytest.mark.regression
@pytest.mark.api
def test_get_robots_id_list(api_client):
    """校验返回的 robot_id 集合必须正好是 {arm1, arm2, arm3}。"""

    robots = _fetch_robots(api_client)
    robots_map = {r.get("robot_id"): r for r in robots}
    expected_ids = {"arm1", "arm2", "arm3"}

    with allure.step("Validate robots set equals {arm1, arm2, arm3}"):
        assert set(robots_map.keys()) == expected_ids, (
            f"Expected robots {expected_ids}, got {set(robots_map.keys())}"
        )


@allure.feature("Tele-Op")
@allure.story("Robots status")
@allure.title("test_get_robots_queue_length")
@pytest.mark.regression
@pytest.mark.api
def test_get_robots_queue_length(api_client):
    """校验 arm1/arm2/arm3 的 queue_length 均不为 0。"""

    robots = _fetch_robots(api_client)
    robots_map = {r.get("robot_id"): r for r in robots}
    expected_ids = {"arm1", "arm2", "arm3"}

    with allure.step("Validate each robot.queue_length is non-zero"):
        for rid in expected_ids:
            r = robots_map.get(rid)
            assert r is not None, f"Robot {rid} not found in response"
            assert isinstance(r.get("queue_length"), int)
            assert r["queue_length"] != 0, f"{rid}.queue_length should not be 0"


@allure.feature("Tele-Op")
@allure.story("Robots status")
@allure.title("test_get_robots_streamid")
@pytest.mark.regression
@pytest.mark.api
def test_get_robots_streamid(api_client):
    """校验 arm1/arm2/arm3 的 youtube_stream_id 精确匹配预期。"""

    robots = _fetch_robots(api_client)
    robots_map = {r.get("robot_id"): r for r in robots}
    expected_streams = {
        "arm1": "YfYeCJjdBqE",
        "arm2": "ui-aIXF36Xg",
        "arm3": "sp4Izv7NvAU",
    }

    with allure.step("Validate each robot.youtube_stream_id matches expected value"):
        for rid, expected_stream in expected_streams.items():
            r = robots_map.get(rid)
            assert r is not None, f"Robot {rid} not found in response"
            assert r.get("youtube_stream_id") == expected_stream, (
                f"{rid}.youtube_stream_id expected {expected_stream}, "
                f"got {r.get('youtube_stream_id')}"
            )


