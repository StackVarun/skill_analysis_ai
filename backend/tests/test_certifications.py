"""Tests for certification APIs."""
import pytest
import json


class TestCertifications:
    """Test certification endpoints."""

    def test_list_certifications_empty(self, client, auth_headers, student_profile_id):
        """Test listing certifications when none exist."""
        response = client.get("/api/students/certifications", headers=auth_headers)
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data == []

    def test_create_certification(self, client, auth_headers, student_profile_id):
        """Test creating a certification."""
        cert_data = {
            "name": "AWS Certified Solutions Architect",
            "issuing_organization": "Amazon Web Services",
            "issue_date": "2024-01-15",
            "expiry_date": "2027-01-15",
            "credential_id": "AWS123456",
            "credential_url": "https://aws.amazon.com/verification",
            "description": "Cloud architecture certification"
        }
        response = client.post("/api/students/certifications",
                             data=json.dumps(cert_data),
                             headers=auth_headers,
                             content_type="application/json")
        assert response.status_code == 201
        data = json.loads(response.data)
        assert data["name"] == "AWS Certified Solutions Architect"
        assert data["issuing_organization"] == "Amazon Web Services"

    def test_get_certification(self, client, auth_headers, student_profile_id):
        """Test getting a specific certification."""
        cert_data = {
            "name": "Test Cert",
            "issuing_organization": "Test Org",
            "issue_date": "2024-01-01"
        }
        create_resp = client.post("/api/students/certifications",
                                data=json.dumps(cert_data),
                                headers=auth_headers,
                                content_type="application/json")
        cert_id = json.loads(create_resp.data)["id"]
        
        response = client.get(f"/api/students/certifications/{cert_id}", headers=auth_headers)
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["name"] == "Test Cert"

    def test_update_certification(self, client, auth_headers, student_profile_id):
        """Test updating a certification."""
        cert_data = {"name": "Original", "issuing_organization": "Test Org", "issue_date": "2024-01-01"}
        create_resp = client.post("/api/students/certifications",
                                data=json.dumps(cert_data),
                                headers=auth_headers,
                                content_type="application/json")
        cert_id = json.loads(create_resp.data)["id"]
        
        update_data = {"name": "Updated", "credential_id": "NEW123"}
        response = client.put(f"/api/students/certifications/{cert_id}",
                            data=json.dumps(update_data),
                            headers=auth_headers,
                            content_type="application/json")
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["name"] == "Updated"
        assert data["credential_id"] == "NEW123"

    def test_delete_certification(self, client, auth_headers, student_profile_id):
        """Test deleting a certification."""
        cert_data = {"name": "To Delete", "issuing_organization": "Test Org", "issue_date": "2024-01-01"}
        create_resp = client.post("/api/students/certifications",
                                data=json.dumps(cert_data),
                                headers=auth_headers,
                                content_type="application/json")
        cert_id = json.loads(create_resp.data)["id"]
        
        response = client.delete(f"/api/students/certifications/{cert_id}", headers=auth_headers)
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["message"] == "Certification deleted successfully"

    def test_certification_authorization_industry(self, client, industry_auth_headers):
        """Test that industry users cannot access student certifications."""
        response = client.get("/api/students/certifications", headers=industry_auth_headers)
        assert response.status_code == 403