"""Tests for experience APIs."""
import pytest
import json


class TestExperience:
    """Test experience endpoints."""

    def test_list_experience_empty(self, client, auth_headers, student_profile_id):
        """Test listing experience when none exist."""
        response = client.get("/api/students/experience", headers=auth_headers)
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data == []

    def test_create_experience(self, client, auth_headers, student_profile_id, skill_id):
        """Test creating an experience."""
        exp_data = {
            "organization": "Tech Corp",
            "job_title": "Software Engineer Intern",
            "employment_type": "INTERNSHIP",
            "location": "San Francisco, CA",
            "start_date": "2023-06-01",
            "end_date": "2023-08-31",
            "description": "Developed backend APIs",
            "skill_ids": [skill_id]
        }
        response = client.post("/api/students/experience",
                             data=json.dumps(exp_data),
                             headers=auth_headers,
                             content_type="application/json")
        assert response.status_code == 201
        data = json.loads(response.data)
        assert data["organization"] == "Tech Corp"
        assert data["employment_type"] == "INTERNSHIP"

    def test_get_experience(self, client, auth_headers, student_profile_id, skill_id):
        """Test getting a specific experience."""
        exp_data = {
            "organization": "Test Corp",
            "job_title": "Developer",
            "start_date": "2023-01-01",
            "skill_ids": [skill_id]
        }
        create_resp = client.post("/api/students/experience",
                                data=json.dumps(exp_data),
                                headers=auth_headers,
                                content_type="application/json")
        exp_id = json.loads(create_resp.data)["id"]
        
        response = client.get(f"/api/students/experience/{exp_id}", headers=auth_headers)
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["organization"] == "Test Corp"

    def test_update_experience(self, client, auth_headers, student_profile_id, skill_id):
        """Test updating an experience."""
        exp_data = {
            "organization": "Original Corp",
            "job_title": "Intern",
            "start_date": "2023-01-01",
            "skill_ids": [skill_id]
        }
        create_resp = client.post("/api/students/experience",
                                data=json.dumps(exp_data),
                                headers=auth_headers,
                                content_type="application/json")
        exp_id = json.loads(create_resp.data)["id"]
        
        update_data = {"organization": "Updated Corp", "employment_type": "FULL_TIME"}
        response = client.put(f"/api/students/experience/{exp_id}",
                            data=json.dumps(update_data),
                            headers=auth_headers,
                            content_type="application/json")
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["organization"] == "Updated Corp"
        assert data["employment_type"] == "FULL_TIME"

    def test_delete_experience(self, client, auth_headers, student_profile_id, skill_id):
        """Test deleting an experience."""
        exp_data = {
            "organization": "To Delete",
            "job_title": "Intern",
            "start_date": "2023-01-01",
            "skill_ids": [skill_id]
        }
        create_resp = client.post("/api/students/experience",
                                data=json.dumps(exp_data),
                                headers=auth_headers,
                                content_type="application/json")
        exp_id = json.loads(create_resp.data)["id"]
        
        response = client.delete(f"/api/students/experience/{exp_id}", headers=auth_headers)
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["message"] == "Experience deleted successfully"

    def test_experience_validation_employment_type(self, client, auth_headers, student_profile_id, skill_id):
        """Test employment type validation."""
        exp_data = {
            "organization": "Test Corp",
            "job_title": "Developer",
            "start_date": "2023-01-01",
            "employment_type": "INVALID",
            "skill_ids": [skill_id]
        }
        response = client.post("/api/students/experience",
                             data=json.dumps(exp_data),
                             headers=auth_headers,
                             content_type="application/json")
        assert response.status_code == 400
        data = json.loads(response.data)
        assert "employment_type" in data["messages"]

    def test_experience_authorization_industry(self, client, industry_auth_headers):
        """Test that industry users cannot access student experience."""
        response = client.get("/api/students/experience", headers=industry_auth_headers)
        assert response.status_code == 403