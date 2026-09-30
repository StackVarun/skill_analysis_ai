"""Tests for student profile APIs."""
import pytest
import json


class TestStudentProfile:
    """Test student profile endpoints."""

    def test_get_profile_created_with_student_account(self, client, auth_headers):
        """A registered student has the profile row required by student APIs."""
        response = client.get("/api/students/profile", headers=auth_headers)
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["full_name"] == "Test Student"

    def test_create_profile(self, client, auth_headers, student_profile_id):
        """Test creating a student profile."""
        profile_data = {
            "full_name": "Test Student",
            "institution": "Test University",
            "degree": "B.Tech",
            "branch": "Computer Science",
            "graduation_year": 2025,
            "cgpa": 8.5,
            "bio": "Test bio",
            "location": "Test City",
            "linkedin_url": "https://linkedin.com/in/teststudent",
            "github_url": "https://github.com/teststudent",
            "portfolio_url": "https://teststudent.dev"
        }
        response = client.put("/api/students/profile",
                            data=json.dumps(profile_data),
                            headers=auth_headers,
                            content_type="application/json")
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["full_name"] == "Test Student"
        assert data["institution"] == "Test University"
        assert data["graduation_year"] == 2025
        assert data["cgpa"] == 8.5

    def test_update_profile(self, client, auth_headers, student_profile_id):
        """Test updating a student profile."""
        # First create
        profile_data = {"full_name": "Original Name"}
        client.put("/api/students/profile",
                  data=json.dumps(profile_data),
                  headers=auth_headers,
                  content_type="application/json")
        
        # Then update
        update_data = {"full_name": "Updated Name", "cgpa": 9.0}
        response = client.put("/api/students/profile",
                            data=json.dumps(update_data),
                            headers=auth_headers,
                            content_type="application/json")
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["full_name"] == "Updated Name"
        assert data["cgpa"] == 9.0

    def test_profile_validation_graduation_year(self, client, auth_headers, student_profile_id):
        """Test graduation year validation."""
        profile_data = {"graduation_year": 1800}
        response = client.put("/api/students/profile",
                            data=json.dumps(profile_data),
                            headers=auth_headers,
                            content_type="application/json")
        assert response.status_code == 400
        data = json.loads(response.data)
        assert "graduation_year" in data["messages"]

    def test_profile_validation_cgpa(self, client, auth_headers, student_profile_id):
        """Test CGPA validation."""
        profile_data = {"cgpa": 11.0}
        response = client.put("/api/students/profile",
                            data=json.dumps(profile_data),
                            headers=auth_headers,
                            content_type="application/json")
        assert response.status_code == 400
        data = json.loads(response.data)
        assert "cgpa" in data["messages"]

    def test_profile_validation_linkedin_url(self, client, auth_headers, student_profile_id):
        """Test LinkedIn URL validation."""
        profile_data = {"linkedin_url": "https://google.com"}
        response = client.put("/api/students/profile",
                            data=json.dumps(profile_data),
                            headers=auth_headers,
                            content_type="application/json")
        assert response.status_code == 400
        data = json.loads(response.data)
        assert "linkedin_url" in data["messages"]

    def test_profile_authorization_industry(self, client, industry_auth_headers):
        """Test that industry users cannot access student profile."""
        response = client.get("/api/students/profile", headers=industry_auth_headers)
        assert response.status_code == 403
        data = json.loads(response.data)
        assert data["error"] == "Forbidden"
