"""Tests for internship APIs."""
import pytest
import json


class TestInternships:
    """Test internship endpoints."""

    def test_list_internships_empty(self, client, auth_headers, student_profile_id):
        """Test listing internships when none exist."""
        response = client.get("/api/students/internships", headers=auth_headers)
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data == []

    def test_create_internship(self, client, auth_headers, student_profile_id, skill_id):
        """Test creating an internship."""
        internship_data = {
            "organization": "Google",
            "role": "Software Engineering Intern",
            "start_date": "2023-05-01",
            "end_date": "2023-08-15",
            "description": "Worked on search infrastructure",
            "certificate_url": "https://google.com/cert",
            "internship_type": "SUMMER",
            "status": "COMPLETED",
            "skill_ids": [skill_id]
        }
        response = client.post("/api/students/internships",
                             data=json.dumps(internship_data),
                             headers=auth_headers,
                             content_type="application/json")
        assert response.status_code == 201
        data = json.loads(response.data)
        assert data["organization"] == "Google"
        assert data["internship_type"] == "SUMMER"
        assert data["status"] == "COMPLETED"

    def test_get_internship(self, client, auth_headers, student_profile_id, skill_id):
        """Test getting a specific internship."""
        internship_data = {
            "organization": "Test Corp",
            "role": "Intern",
            "start_date": "2023-01-01",
            "skill_ids": [skill_id]
        }
        create_resp = client.post("/api/students/internships",
                                data=json.dumps(internship_data),
                                headers=auth_headers,
                                content_type="application/json")
        internship_id = json.loads(create_resp.data)["id"]
        
        response = client.get(f"/api/students/internships/{internship_id}", headers=auth_headers)
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["organization"] == "Test Corp"

    def test_update_internship(self, client, auth_headers, student_profile_id, skill_id):
        """Test updating an internship."""
        internship_data = {
            "organization": "Original Corp",
            "role": "Intern",
            "start_date": "2023-01-01",
            "skill_ids": [skill_id]
        }
        create_resp = client.post("/api/students/internships",
                                data=json.dumps(internship_data),
                                headers=auth_headers,
                                content_type="application/json")
        internship_id = json.loads(create_resp.data)["id"]
        
        update_data = {"organization": "Updated Corp", "status": "ONGOING"}
        response = client.put(f"/api/students/internships/{internship_id}",
                            data=json.dumps(update_data),
                            headers=auth_headers,
                            content_type="application/json")
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["organization"] == "Updated Corp"
        assert data["status"] == "ONGOING"

    def test_delete_internship(self, client, auth_headers, student_profile_id, skill_id):
        """Test deleting an internship."""
        internship_data = {
            "organization": "To Delete",
            "role": "Intern",
            "start_date": "2023-01-01",
            "skill_ids": [skill_id]
        }
        create_resp = client.post("/api/students/internships",
                                data=json.dumps(internship_data),
                                headers=auth_headers,
                                content_type="application/json")
        internship_id = json.loads(create_resp.data)["id"]
        
        response = client.delete(f"/api/students/internships/{internship_id}", headers=auth_headers)
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["message"] == "Internship deleted successfully"

    def test_internship_authorization_industry(self, client, industry_auth_headers):
        """Test that industry users cannot access student internships."""
        response = client.get("/api/students/internships", headers=industry_auth_headers)
        assert response.status_code == 403