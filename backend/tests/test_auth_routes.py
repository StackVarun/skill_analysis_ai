"""Authentication API regression tests."""


def test_registration_validators_accept_marshmallow_context(client):
    response = client.post(
        "/api/auth/register",
        json={
            "email": "new-student@example.com",
            "password": "password123",
            "first_name": "New",
            "last_name": "Student",
        },
    )

    assert response.status_code == 201, response.get_json()
    assert response.get_json()["user"]["email"] == "new-student@example.com"


def test_registration_still_rejects_invalid_email(client):
    response = client.post(
        "/api/auth/register",
        json={
            "email": "not-an-email",
            "password": "password123",
            "first_name": "New",
            "last_name": "Student",
        },
    )

    assert response.status_code == 400
    assert response.get_json()["error"] == "Validation error"
