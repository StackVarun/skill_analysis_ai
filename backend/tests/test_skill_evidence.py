"""Tests for skill evidence APIs."""
import pytest
import json


class TestSkillEvidence:
    """Test skill evidence endpoints."""

    def test_list_skill_evidence_empty(self, client, auth_headers, student_profile_id):
        """Test listing skill evidence when none exist."""
        response = client.get("/api/students/skill-evidence", headers=auth_headers)
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data == []

    def test_create_skill_evidence(self, client, auth_headers, student_profile_id, skill_id):
        """Test creating skill evidence."""
        # First create a project to link to
        project_data = {"title": "Test Project", "skill_ids": [skill_id]}
        create_resp = client.post("/api/students/projects",
                                data=json.dumps(project_data),
                                headers=auth_headers,
                                content_type="application/json")
        project_id = json.loads(create_resp.data)["id"]
        
        evidence_data = {
            "skill_id": skill_id,
            "evidence_type": "PROJECT",
            "evidence_title": "Test Project",
            "description": "Built a test project",
            "project_id": project_id,
            "verification_status": "SELF_REPORTED",
            "evidence_strength": 0.8
        }
        response = client.post("/api/students/skill-evidence",
                             data=json.dumps(evidence_data),
                             headers=auth_headers,
                             content_type="application/json")
        assert response.status_code == 201
        data = json.loads(response.data)
        assert data["skill_id"] == skill_id
        assert data["evidence_type"] == "PROJECT"
        assert data["evidence_strength"] == 0.8

    def test_get_skill_evidence(self, client, auth_headers, student_profile_id, skill_id):
        """Test getting a specific skill evidence."""
        # Create project
        project_data = {"title": "Test Project", "skill_ids": [skill_id]}
        create_resp = client.post("/api/students/projects",
                                data=json.dumps(project_data),
                                headers=auth_headers,
                                content_type="application/json")
        project_id = json.loads(create_resp.data)["id"]
        
        # Create evidence
        evidence_data = {
            "skill_id": skill_id,
            "evidence_type": "PROJECT",
            "evidence_title": "Test Project",
            "project_id": project_id
        }
        create_resp = client.post("/api/students/skill-evidence",
                                data=json.dumps(evidence_data),
                                headers=auth_headers,
                                content_type="application/json")
        evidence_id = json.loads(create_resp.data)["id"]
        
        response = client.get(f"/api/students/skill-evidence/{evidence_id}", headers=auth_headers)
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["evidence_title"] == "Test Project"

    def test_update_skill_evidence(self, client, auth_headers, student_profile_id, skill_id):
        """Test updating skill evidence."""
        project_data = {"title": "Test Project", "skill_ids": [skill_id]}
        create_resp = client.post("/api/students/projects",
                                data=json.dumps(project_data),
                                headers=auth_headers,
                                content_type="application/json")
        project_id = json.loads(create_resp.data)["id"]
        
        evidence_data = {
            "skill_id": skill_id,
            "evidence_type": "PROJECT",
            "evidence_title": "Test Project",
            "project_id": project_id
        }
        create_resp = client.post("/api/students/skill-evidence",
                                data=json.dumps(evidence_data),
                                headers=auth_headers,
                                content_type="application/json")
        evidence_id = json.loads(create_resp.data)["id"]
        
        update_data = {"evidence_strength": 0.9}
        response = client.put(f"/api/students/skill-evidence/{evidence_id}",
                            data=json.dumps(update_data),
                            headers=auth_headers,
                            content_type="application/json")
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["verification_status"] == "SELF_REPORTED"
        assert data["evidence_strength"] == 0.9

    def test_delete_skill_evidence(self, client, auth_headers, student_profile_id, skill_id):
        """Test deleting skill evidence."""
        project_data = {"title": "Test Project", "skill_ids": [skill_id]}
        create_resp = client.post("/api/students/projects",
                                data=json.dumps(project_data),
                                headers=auth_headers,
                                content_type="application/json")
        project_id = json.loads(create_resp.data)["id"]
        
        evidence_data = {
            "skill_id": skill_id,
            "evidence_type": "PROJECT",
            "evidence_title": "Test Project",
            "project_id": project_id
        }
        create_resp = client.post("/api/students/skill-evidence",
                                data=json.dumps(evidence_data),
                                headers=auth_headers,
                                content_type="application/json")
        evidence_id = json.loads(create_resp.data)["id"]
        
        response = client.delete(f"/api/students/skill-evidence/{evidence_id}", headers=auth_headers)
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["message"] == "Skill evidence deleted successfully"

    def test_skill_evidence_validation_evidence_type(self, client, auth_headers, student_profile_id, skill_id):
        """Test evidence type validation."""
        evidence_data = {
            "skill_id": skill_id,
            "evidence_type": "INVALID",
            "evidence_title": "Test"
        }
        response = client.post("/api/students/skill-evidence",
                             data=json.dumps(evidence_data),
                             headers=auth_headers,
                             content_type="application/json")
        assert response.status_code == 400
        data = json.loads(response.data)
        assert "evidence_type" in data["messages"]

    def test_skill_evidence_authorization_industry(self, client, industry_auth_headers):
        """Test that industry users cannot access skill evidence."""
        response = client.get("/api/students/skill-evidence", headers=industry_auth_headers)
        assert response.status_code == 403