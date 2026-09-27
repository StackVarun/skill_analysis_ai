"""Tests for skill APIs."""
import pytest
import json


class TestSkills:
    """Test skill endpoints."""

    def test_list_skills_empty(self, client):
        """Test listing skills when none exist."""
        response = client.get("/api/skills")
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data == []

    def test_create_skill_industry(self, client, industry_auth_headers):
        """Test creating a skill as industry user."""
        skill_data = {
            "name": "Python",
            "category": "Programming",
            "description": "Python programming language"
        }
        response = client.post("/api/skills",
                             data=json.dumps(skill_data),
                             headers=industry_auth_headers,
                             content_type="application/json")
        assert response.status_code == 201
        data = json.loads(response.data)
        assert data["name"] == "Python"
        assert data["category"] == "Programming"

    def test_create_skill_student_forbidden(self, client, auth_headers):
        """Test that students cannot create skills."""
        skill_data = {"name": "Python", "category": "Programming"}
        response = client.post("/api/skills",
                             data=json.dumps(skill_data),
                             headers=auth_headers,
                             content_type="application/json")
        assert response.status_code == 403

    def test_create_duplicate_skill(self, client, industry_auth_headers, skill_id):
        """Test that duplicate skills are prevented."""
        skill_data = {"name": "Python", "category": "Programming"}
        response = client.post("/api/skills",
                             data=json.dumps(skill_data),
                             headers=industry_auth_headers,
                             content_type="application/json")
        assert response.status_code == 400
        data = json.loads(response.data)
        assert "already exists" in data["message"]

    def test_list_skills(self, client, skill_id):
        """Test listing skills."""
        response = client.get("/api/skills")
        assert response.status_code == 200
        data = json.loads(response.data)
        assert len(data) >= 1
        assert any(s["name"] == "Python" for s in data)

    def test_get_skill_by_id(self, client, skill_id):
        """Test getting a skill by ID."""
        response = client.get(f"/api/skills/{skill_id}")
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["name"] == "Python"

    def test_filter_skills_by_category(self, client, skill_id):
        """Test filtering skills by category."""
        response = client.get("/api/skills?category=Programming")
        assert response.status_code == 200
        data = json.loads(response.data)
        assert all(s["category"] == "Programming" for s in data)

    def test_search_skills(self, client, skill_id):
        """Test searching skills."""
        response = client.get("/api/skills?search=Python")
        assert response.status_code == 200
        data = json.loads(response.data)
        assert any(s["name"] == "Python" for s in data)