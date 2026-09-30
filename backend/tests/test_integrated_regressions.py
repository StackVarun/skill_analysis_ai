"""Regressions for student identity and Phase 5/6 API integration."""
from app.services.reference_data_service import ReferenceDataService


def test_student_apis_and_phase56_routes_after_registration(app, client):
    with app.app_context():
        ReferenceDataService.seed()

    registered = client.post("/api/auth/register", json={
        "email": "integration-student@example.com",
        "password": "password123",
        "first_name": "Integration",
        "last_name": "Student",
    })
    assert registered.status_code == 201, registered.get_json()
    headers = {"Authorization": f"Bearer {registered.get_json()['access_token']}"}

    profile = client.get("/api/students/profile", headers=headers)
    assert profile.status_code == 200, profile.get_json()
    assert profile.get_json()["full_name"] == "Integration Student"

    catalog = client.get("/api/skills")
    assert catalog.status_code == 200
    assert len(catalog.get_json()) == 23

    roles = client.get("/api/roles", headers=headers)
    assert roles.status_code == 200
    assert len(roles.get_json()) == 7
    assert all(role["required_skills"] for role in roles.get_json())

    student_skills = client.get("/api/students/skills", headers=headers)
    assert student_skills.status_code == 200
    assert student_skills.get_json() == []

    opportunities = client.get("/api/opportunities", headers=headers)
    assert opportunities.status_code == 200
    assert opportunities.get_json() == []

    passport = client.get("/api/passport/me", headers=headers)
    assert passport.status_code == 200, passport.get_json()
    assert passport.get_json()["student"]["full_name"] == "Integration Student"
