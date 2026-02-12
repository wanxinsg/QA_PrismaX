import pytest
import allure


def _fetch_leaderboard(api_client):
    """Call GET /tele_op/leaderboard and return the user list.

    Supports two response shapes: raw list or {"users": [...]} / {"leaderboard": [...]}.
    """

    with allure.step("Send GET /tele_op/leaderboard"):
        response = api_client.get("/tele_op/leaderboard")

    with allure.step("Validate HTTP status code is 200"):
        assert response.status_code == 200

    data = response.json()
    if isinstance(data, dict) and "leaderboard" in data:
        users = data["leaderboard"]
    elif isinstance(data, list):
        users = data
    elif isinstance(data, dict) and "users" in data:
        users = data["users"]
    else:
        raise AssertionError(f"Unexpected leaderboard response structure: {data}")

    assert isinstance(users, list), "Leaderboard response must be a list of users"
    assert users, "Leaderboard list should not be empty"
    return users


@allure.feature("Tele-Op")
@allure.story("Leaderboard")
@allure.title("test_leaderboard")
@pytest.mark.regression
@pytest.mark.api
def test_leaderboard(api_client):
    """Validate leaderboard: required fields, top 50, ranks 1-50 continuous, sorted by total_points descending."""

    users = _fetch_leaderboard(api_client)

    with allure.step("Validate user entries contain required fields"):
        for idx, u in enumerate(users):
            assert "user_id" in u, f"user[{idx}] missing 'user_id'"
            assert "total_points" in u, f"user[{idx}] missing 'total_points'"
            assert "rank" in u, f"user[{idx}] missing 'rank'"
            assert "controlled_hours" in u, f"user[{idx}] missing 'controlled_hours'"

    with allure.step("Validate leaderboard has at least top 50 users"):
        assert len(users) >= 50, (
            f"Leaderboard should have at least 50 users, got {len(users)}"
        )

    with allure.step("Validate ranks from 1 to 50 are continuous"):
        top50 = users[:50]
        ranks = [u.get("rank") for u in top50]
        expected_ranks = list(range(1, 51))
        assert ranks == expected_ranks, (
            f"Expected ranks 1..50, got {ranks}"
        )

    with allure.step("Validate leaderboard is sorted by total_points descending"):
        points = [u.get("total_points") for u in users]
        sorted_points = sorted(points, reverse=True)
        assert points == sorted_points, (
            "Leaderboard is not sorted by total_points descending"
        )
