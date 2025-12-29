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
@allure.title("test_get_live_paused_status")
@pytest.mark.regression
@pytest.mark.api
def test_get_live_paused_status(api_client):
    """检查 robots 列表包含 arm1/arm2/arm3 三个机器人，且 live_paused 均为 False。"""

    robots = _fetch_robots(api_client)
    robots_map = {r.get("robot_id"): r for r in robots}
    expected_ids = {"arm1", "arm2", "arm3"}

    with allure.step("Validate robots list contains exactly three arms"):
        assert set(robots_map.keys()) == expected_ids, (
            f"Expected robots {expected_ids}, got {set(robots_map.keys())}"
        )

    with allure.step("Validate each robot.live_paused is False"):
        for rid in expected_ids:
            r = robots_map.get(rid)
            assert r is not None, f"Robot {rid} not found in response"
            assert r.get("live_paused") is False, f"{rid}.live_paused must be False"
