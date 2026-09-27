"""Tests for project APIs."""
import pytest
import json


class TestProjects:
    """Test project endpoints."""

    def test_list_projects_empty(self, client, auth_headers, student_profile_id):
        """Test listing projects when none exist."""
        response = client.get("/api/students/projects", headers=auth_headers)
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data == []

    def test_create_project(self, client, auth_headers, student_profile_id, skill_id):
        """Test creating a project."""
        project_data = {
            "title": "E-commerce Website",
            "description": "Full-stack e-commerce platform",
            "technologies": "Python, React, PostgreSQL",
            "project_url": "https://example.com",
            "github_url": "https://github.com/testuser/ecommerce",
            "start_date": "2024-01-01",
            "end_date": "2024-03-01",
            "role": "Full-stack Developer",
            "skill_ids": [skill_id]
        }
        response = client.post("/api/students/projects",
                             data=json.dumps(project_data),
                             headers=auth_headers,
                             content_type="application/json")
        assert response.status_code == 201
        data = json.loads(response.data)
        assert data["title"] == "E-commerce Website"
        assert len(data["skills"]) == 1

    def test_get_project(self, client, auth_headers, student_profile_id, skill_id):
        """Test getting a specific project."""
        project_data = {
            "title": "Test Project",
            "skill_ids": [skill_id]
        }
        create_resp = client.post("/api/students/projects",
                                data=json.dumps(project_data),
                                headers=auth_headers,
                                content_type="application/json")
        project_id = json.loads(create_resp.data)["id"]
        
        response = client.get(f"/api/students/projects/{project_id}", headers=auth_headers)
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["title"] == "Test Project"

    def test_update_project(self, client, auth_headers, student_profile_id, skill_id):
        """Test updating a project."""
        project_data = {"title": "Original Title", "skill_ids": [skill_id]}
        create_resp = client.post("/api/students/projects",
                                data=json.dumps(project_data),
                                headers=auth_headers,
                                content_type="application/json")
        project_id = json.loads(create_resp.data)["id"]
        
        update_data = {"title": "Updated Title", "role": "Lead Developer"}
        response = client.put(f"/api/students/projects/{project_id}",
                            data=json.dumps(update_data),
                            headers=auth_headers,
                            content_type="application/json")
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["title"] == "Updated Title"
        assert data["role"] == "Lead Developer"

    def test_delete_project(self, client, auth_headers, student_profile_id, skill_id):
        """Test deleting a project."""
        project_data = {"title": "To Delete", "skill_ids": [skill_id]}
        create_resp = client.post("/api/students/projects",
                                data=json.dumps(project_data),
                                headers=auth_headers,
                                content_type="application/json")
        project_id = json.loads(create_resp.data)["id"]
        
        response = client.delete(f"/api/students/projects/{project_id}", headers=auth_headers)
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["message"] == "Project deleted successfully"
        
        # Verify it's gone
        response = client.get("/api/students/projects", headers=auth_headers)
        data = json.loads(response.data)
        assert len(data) == 0

    def test_project_authorization_industry(self, client, industry_auth_headers):
        """Test that industry users cannot access student projects."""
        response = client.get("/api/students/projects", headers=industry_auth_headers)
        assert response.status_code == 403