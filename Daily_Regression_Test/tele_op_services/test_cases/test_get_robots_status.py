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
    """Assert response is 200 and contains the configured robot ID."""

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
    """Assert robot_id set is exactly {arm1, arm2, arm3, arm4}."""

    robots = _fetch_robots(api_client)
    robots_map = {r.get("robot_id"): r for r in robots}
    expected_ids = {"arm1", "arm2", "arm3", "arm4"}

    with allure.step("Validate robots set equals {arm1, arm2, arm3, arm4}"):
        assert set(robots_map.keys()) == expected_ids, (
            f"Expected robots {expected_ids}, got {set(robots_map.keys())}"
        )


@allure.feature("Tele-Op")
@allure.story("Robots status")
@allure.title("test_get_robots_queue_length")
@pytest.mark.regression
@pytest.mark.api
def test_get_robots_queue_length(api_client):
    """Assert queue_length is non-zero for arm1/arm2/arm3/arm4."""

    robots = _fetch_robots(api_client)
    robots_map = {r.get("robot_id"): r for r in robots}
    expected_ids = {"arm1", "arm2", "arm3", "arm4"}

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
    """Assert youtube_stream_id is non-empty for arm1/arm2/arm3/arm4."""

    robots = _fetch_robots(api_client)
    robots_map = {r.get("robot_id"): r for r in robots}
    expected_ids = {"arm1", "arm2", "arm3", "arm4"}

    with allure.step("Validate each robot.youtube_stream_id is non-empty"):
        for rid in expected_ids:
            r = robots_map.get(rid)
            assert r is not None, f"Robot {rid} not found in response"
            stream_id = r.get("youtube_stream_id")
            assert stream_id is not None, f"{rid}.youtube_stream_id should not be None"
            assert isinstance(stream_id, str), f"{rid}.youtube_stream_id should be a string"
            assert stream_id.strip(), f"{rid}.youtube_stream_id should not be empty"


