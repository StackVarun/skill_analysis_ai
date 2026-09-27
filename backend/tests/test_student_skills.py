"""Tests for student skill APIs."""
import pytest
import json


class TestStudentSkills:
    """Test student skill endpoints."""

    def test_list_student_skills_empty(self, client, auth_headers, student_profile_id):
        """Test listing student skills when none exist."""
        response = client.get("/api/students/skills", headers=auth_headers)
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data == []

    def test_add_student_skill(self, client, auth_headers, student_profile_id, skill_id):
        """Test adding a skill to student profile."""
        skill_data = {
            "skill_id": skill_id,
            "proficiency": "INTERMEDIATE",
            "years_experience": 2,
            "months_experience": 6,
            "source": "Coursework"
        }
        response = client.post("/api/students/skills",
                             data=json.dumps(skill_data),
                             headers=auth_headers,
                             content_type="application/json")
        assert response.status_code == 201
        data = json.loads(response.data)
        assert data["skill_id"] == skill_id
        assert data["proficiency"] == "INTERMEDIATE"
        assert data["years_experience"] == 2

    def test_add_duplicate_student_skill(self, client, auth_headers, student_profile_id, skill_id):
        """Test that duplicate student skills are prevented."""
        skill_data = {"skill_id": skill_id, "proficiency": "BEGINNER"}
        client.post("/api/students/skills",
                   data=json.dumps(skill_data),
                   headers=auth_headers,
                   content_type="application/json")
        
        response = client.post("/api/students/skills",
                             data=json.dumps(skill_data),
                             headers=auth_headers,
                             content_type="application/json")
        assert response.status_code == 400
        data = json.loads(response.data)
        assert "already has this skill" in data["message"]

    def test_update_student_skill(self, client, auth_headers, student_profile_id, skill_id):
        """Test updating student skill proficiency."""
        skill_data = {"skill_id": skill_id, "proficiency": "BEGINNER"}
        client.post("/api/students/skills",
                   data=json.dumps(skill_data),
                   headers=auth_headers,
                   content_type="application/json")
        
        update_data = {"proficiency": "ADVANCED", "years_experience": 3}
        response = client.put(f"/api/students/skills/{skill_id}",
                            data=json.dumps(update_data),
                            headers=auth_headers,
                            content_type="application/json")
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["proficiency"] == "ADVANCED"
        assert data["years_experience"] == 3

    def test_remove_student_skill(self, client, auth_headers, student_profile_id, skill_id):
        """Test removing a student skill."""
        skill_data = {"skill_id": skill_id, "proficiency": "BEGINNER"}
        client.post("/api/students/skills",
                   data=json.dumps(skill_data),
                   headers=auth_headers,
                   content_type="application/json")
        
        response = client.delete(f"/api/students/skills/{skill_id}",
                               headers=auth_headers)
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["message"] == "Skill removed successfully"
        
        # Verify it's gone
        response = client.get("/api/students/skills", headers=auth_headers)
        data = json.loads(response.data)
        assert len(data) == 0

    def test_student_skill_validation_proficiency(self, client, auth_headers, student_profile_id, skill_id):
        """Test proficiency validation."""
        skill_data = {"skill_id": skill_id, "proficiency": "INVALID"}
        response = client.post("/api/students/skills",
                             data=json.dumps(skill_data),
                             headers=auth_headers,
                             content_type="application/json")
        assert response.status_code == 400
        data = json.loads(response.data)
        assert "proficiency" in data["messages"]

    def test_student_skill_authorization_industry(self, client, industry_auth_headers):
        """Test that industry users cannot access student skills."""
        response = client.get("/api/students/skills", headers=industry_auth_headers)
        assert response.status_code == 403