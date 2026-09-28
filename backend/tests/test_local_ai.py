"""Local AI APIs remain useful and safe with mocked or missing runtimes."""
import json
from unittest.mock import patch

from app.extensions import db
from app.models.resume import Resume
from app.models.role import Role, RoleSkillRequirement
from app.models.skill import Skill
from app.models.skill_evidence import SkillEvidence, VerificationStatus
from app.models.student_skill import StudentSkill
from app.services.local_ai_service import LocalAIService, LocalModelError, OllamaAdapter


class FakeAdapter:
    def __init__(self, response=None, error=None):
        self.response = response
        self.error = error

    def generate_json(self, prompt):
        if self.error:
            raise self.error
        return self.response


def test_resume_extraction_is_suggestion_only(client, app, auth_headers, student_profile_id, skill_id):
    with app.app_context():
        resume = Resume(student_id=student_profile_id, filename="resume.pdf", file_type="pdf", file_path="unused")
        resume.extracted_text = "Built APIs using Python and Flask."
        db.session.add(resume)
        db.session.add(StudentSkill(student_id=student_profile_id, skill_id=skill_id, proficiency="INTERMEDIATE"))
        db.session.add(SkillEvidence(student_id=student_profile_id, skill_id=skill_id, evidence_type="PROJECT",
                                     evidence_title="Verified project", verification_status=VerificationStatus.VERIFIED))
        db.session.commit()
        resume_id = resume.id
    with patch("app.routes.ai_routes.ai_service", LocalAIService(FakeAdapter({"skills": [{"name": "Python", "evidence": "using Python"}]}))):
        response = client.post("/api/ai/resume-skills/extract", headers=auth_headers, json={"resume_id": resume_id})
    assert response.status_code == 200
    assert response.json["skills"][0]["source"] == "resume_ai_extraction"
    assert response.json["skills"][0]["verified"] is False
    assert response.json["skills"][0]["already_verified"] is True
    assert response.json["skills"][0]["already_on_student_profile"] is True
    assert response.json["persisted"] is False


def test_normalization_only_returns_catalog_skills(client, auth_headers, app, skill_id, student_profile_id):
    with patch("app.routes.ai_routes.ai_service", LocalAIService(FakeAdapter({"normalized_skill": "Python"}))):
        response = client.post("/api/ai/skills/normalize", headers=auth_headers, json={"variant": "Py"})
    assert response.status_code == 200
    assert response.json["skill_id"] == skill_id
    assert response.json["validated_against_catalog"] is True
    assert response.json["persisted"] is False


def test_gap_explanation_preserves_phase3_numbers(client, app, auth_headers, student_profile_id, skill_id):
    with app.app_context():
        skill = Skill.query.get(skill_id)
        db.session.add(StudentSkill(student_id=student_profile_id, skill_id=skill_id, proficiency="INTERMEDIATE"))
        role = Role(name="AI Test Role")
        role.requirements.append(RoleSkillRequirement(skill_id=skill.id, required_proficiency=80, weight=1))
        db.session.add(role)
        db.session.commit()
        role_id = role.id
    with patch("app.routes.ai_routes.ai_service", LocalAIService(FakeAdapter({"explanations": [{"skill_id": skill_id, "explanation": "Practice Python functions and data structures."}]}))):
        response = client.post("/api/ai/skill-gaps/explain", headers=auth_headers, json={"role_id": role_id})
    assert response.status_code == 200
    row = response.json["skill_gaps"][0]
    assert (row["student_score"], row["required_score"], row["gap"]) == (30, 80, 50)
    assert row["explanation"].startswith("Practice Python")


def test_roadmap_uses_phase3_gaps_and_fallback_on_bad_output(client, app, auth_headers, student_profile_id, skill_id):
    with app.app_context():
        skill = Skill.query.get(skill_id)
        db.session.add(StudentSkill(student_id=student_profile_id, skill_id=skill_id, proficiency="BEGINNER"))
        role = Role(name="Roadmap Role")
        role.requirements.append(RoleSkillRequirement(skill_id=skill.id, required_proficiency=90, weight=1))
        db.session.add(role); db.session.commit(); role_id = role.id
    with patch("app.routes.ai_routes.ai_service", LocalAIService(FakeAdapter({"steps": "not a list"}))):
        response = client.post("/api/ai/learning-roadmap", headers=auth_headers, json={"role_id": role_id})
    assert response.status_code == 200
    assert response.json["status"] == "fallback"
    assert response.json["phase3_gaps"][0]["gap"] == 75
    assert response.json["steps"][0]["priority"] == "high"
    good_step = {"steps": [{"skill_id": skill_id, "sequence": 1, "title": "Strengthen Python fundamentals", "topics": ["Functions", "Collections"]}]}
    with patch("app.routes.ai_routes.ai_service", LocalAIService(FakeAdapter(good_step))):
        ai_response = client.post("/api/ai/learning-roadmap", headers=auth_headers, json={"role_id": role_id})
    assert ai_response.json["status"] == "ok"
    assert ai_response.json["phase3_gaps"][0]["gap"] == 75
    assert ai_response.json["steps"][0]["priority"] == "high"


def test_unavailable_runtime_and_invalid_input_fallback(client, auth_headers, skill_id, student_profile_id):
    with patch("app.routes.ai_routes.ai_service", LocalAIService(FakeAdapter(error=LocalModelError("offline")))):
        response = client.post("/api/ai/skills/normalize", headers=auth_headers, json={"variant": "Py"})
    assert response.status_code == 200
    assert response.json["status"] == "fallback"
    assert response.json["normalized_skill"] == "Python"
    assert client.post("/api/ai/skills/normalize", headers=auth_headers, json={"variant": ""}).status_code == 400


def test_ai_endpoints_require_authentication(client):
    assert client.post("/api/ai/skills/normalize", json={"variant": "JS"}).status_code == 401


def test_non_student_cannot_use_student_ai_endpoints(client, industry_auth_headers):
    assert client.post("/api/ai/skills/normalize", headers=industry_auth_headers, json={"variant": "JS"}).status_code == 403


def test_ollama_adapter_reports_model_loading_failure(app):
    class FakeResponse:
        def __enter__(self): return self
        def __exit__(self, *args): return False
        def read(self): return json.dumps({"error": "model missing"}).encode()
    with app.app_context(), patch("app.services.local_ai_service.urlopen", return_value=FakeResponse()):
        try:
            OllamaAdapter().generate_json("test")
            assert False, "expected a model loading error"
        except LocalModelError:
            pass


def test_untrusted_extraction_output_falls_back_to_catalog(client, app, auth_headers, student_profile_id, skill_id):
    with app.app_context():
        resume = Resume(student_id=student_profile_id, filename="resume.pdf", file_type="pdf", file_path="unused")
        resume.extracted_text = "Python services"
        db.session.add(resume); db.session.commit(); resume_id = resume.id
    bad_output = {"skills": [{"name": "UnknownSkill", "evidence": "hallucinated"}]}
    with patch("app.routes.ai_routes.ai_service", LocalAIService(FakeAdapter(bad_output))):
        response = client.post("/api/ai/resume-skills/extract", headers=auth_headers, json={"resume_id": resume_id})
    assert response.status_code == 200
    assert response.json["status"] == "fallback"
    assert response.json["skills"][0]["skill_id"] == skill_id
    assert response.json["skills"][0]["source"] == "resume_catalog_match"


def test_empty_malformed_and_timeout_model_responses(app):
    class FakeResponse:
        def __init__(self, body): self.body = body
        def __enter__(self): return self
        def __exit__(self, *args): return False
        def read(self): return self.body
    with app.app_context():
        for body in (b'{"response":""}', b'{"response":"not json"}'):
            with patch("app.services.local_ai_service.urlopen", return_value=FakeResponse(body)):
                try:
                    OllamaAdapter().generate_json("test")
                    assert False, "expected malformed or empty response error"
                except LocalModelError:
                    pass
        with patch("app.services.local_ai_service.urlopen", side_effect=TimeoutError()):
            try:
                OllamaAdapter().generate_json("test")
                assert False, "expected timeout error"
            except LocalModelError:
                pass
        app.config["LOCAL_AI_BASE_URL"] = "https://example.com"
        try:
            OllamaAdapter().generate_json("test")
            assert False, "expected loopback-only URL validation"
        except LocalModelError:
            pass
