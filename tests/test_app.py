from copy import deepcopy

import pytest
from fastapi.testclient import TestClient

import src.app as app_module


client = TestClient(app_module.app)


@pytest.fixture(autouse=True)
def restore_activities():
    original_activities = deepcopy(app_module.activities)
    yield
    app_module.activities.clear()
    app_module.activities.update(original_activities)


def test_root_redirects_to_frontend():
    # Arrange
    expected_redirect = "/static/index.html"

    # Act
    response = client.get("/", follow_redirects=False)

    # Assert
    assert response.status_code == 307
    assert response.headers["location"] == expected_redirect


def test_get_activities_returns_activity_details():
    # Arrange
    expected_activity = "Chess Club"

    # Act
    response = client.get("/activities")

    # Assert
    assert response.status_code == 200
    activities = response.json()
    assert expected_activity in activities
    assert activities[expected_activity] == {
        "description": "Learn strategies and compete in chess tournaments",
        "schedule": "Fridays, 3:30 PM - 5:00 PM",
        "max_participants": 12,
        "participants": ["michael@mergington.edu", "daniel@mergington.edu"],
    }


def test_signup_adds_participant():
    # Arrange
    activity = "Chess Club"
    email = "new@mergington.edu"

    # Act
    response = client.post(
        f"/activities/{activity}/signup", params={"email": email}
    )

    # Assert
    assert response.status_code == 200
    assert response.json() == {"message": f"Signed up {email} for {activity}"}
    assert email in app_module.activities[activity]["participants"]


def test_signup_supports_activity_names_with_spaces():
    # Arrange
    activity = "Programming Class"
    email = "new@mergington.edu"

    # Act
    response = client.post(
        f"/activities/{activity}/signup",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 200


def test_signup_rejects_unknown_activity():
    # Arrange
    activity = "Unknown Club"
    email = "new@mergington.edu"

    # Act
    response = client.post(
        f"/activities/{activity}/signup", params={"email": email}
    )

    # Assert
    assert response.status_code == 404
    assert response.json() == {"detail": "Activity not found"}


def test_signup_rejects_duplicate_participant():
    # Arrange
    activity = "Chess Club"
    email = "michael@mergington.edu"

    # Act
    response = client.post(
        f"/activities/{activity}/signup",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 400
    assert response.json() == {
        "detail": "Student is already signed up for this activity"
    }


def test_signup_requires_email():
    # Arrange
    activity = "Chess Club"

    # Act
    response = client.post(f"/activities/{activity}/signup")

    # Assert
    assert response.status_code == 422


def test_unregister_removes_participant():
    # Arrange
    activity = "Chess Club"
    email = "michael@mergington.edu"

    # Act
    response = client.delete(
        f"/activities/{activity}/participants/{email}"
    )

    # Assert
    assert response.status_code == 200
    assert response.json() == {"message": f"Unregistered {email} from {activity}"}
    assert email not in app_module.activities[activity]["participants"]


def test_unregister_rejects_unknown_activity():
    # Arrange
    activity = "Unknown Club"
    email = "student@mergington.edu"

    # Act
    response = client.delete(
        f"/activities/{activity}/participants/{email}"
    )

    # Assert
    assert response.status_code == 404
    assert response.json() == {"detail": "Activity not found"}


def test_unregister_rejects_missing_participant():
    # Arrange
    activity = "Chess Club"
    email = "missing@mergington.edu"

    # Act
    response = client.delete(
        f"/activities/{activity}/participants/{email}"
    )

    # Assert
    assert response.status_code == 404
    assert response.json() == {
        "detail": "Student is not signed up for this activity"
    }