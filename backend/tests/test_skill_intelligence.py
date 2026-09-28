"""Tests for deterministic Phase 3 skill intelligence."""
import pytest
from app.extensions import db
from app.models.skill import Skill
from app.models.student_skill import StudentSkill
from app.models.skill_evidence import SkillEvidence
from app.models.project import Project
from app.models.role import Role, RoleSkillRequirement
from app.services.skill_intelligence_service import SkillIntelligenceService as Service


def test_assessment_create_submit_and_score(client, app, industry_auth_headers, auth_headers, student_profile_id, skill_id):
    response = client.post("/api/assessments", headers=industry_auth_headers, json={
        "title": "Python basics", "skill_id": skill_id,
        "questions": [{"skill_id": skill_id, "prompt": "2+2?", "options": ["4", "5"], "correct_answer": "4"}]
    })
    assert response.status_code == 201
    aid = response.json["id"]
    qid = response.json["questions"][0]["id"]
    submitted = client.post(f"/api/assessments/{aid}/submit", headers=auth_headers, json={"answers": [{"question_id": qid, "answer": "4"}]})
    assert submitted.status_code == 201
    assert submitted.json["score"] == 100
    assert client.post(f"/api/assessments/{aid}/submit", headers=auth_headers, json={"answers": [{"question_id": qid, "answer": "4"}]}).status_code == 400


def test_assessment_validation_and_student_isolation(client, app, industry_auth_headers, auth_headers, student_profile_id, skill_id):
    payload = {"title": "Python basics", "skill_id": skill_id, "questions": [{"skill_id": skill_id, "prompt": "Q?", "options": ["a", "b"], "correct_answer": "a"}]}
    aid = client.post("/api/assessments", headers=industry_auth_headers, json=payload).json["id"]
    qid = client.get(f"/api/assessments/{aid}", headers=auth_headers).json["questions"][0]["id"]
    assert client.post(f"/api/assessments/{aid}/submit", headers=auth_headers, json={"answers": [{"question_id": qid + 500, "answer": "a"}]}).status_code == 400
    with app.app_context():
        from app.models.user import User
        from app.models.student_profile import StudentProfile
        from flask_jwt_extended import create_access_token
        other = User(email="other@test.com", password="password123", first_name="Other", last_name="Student", role="STUDENT")
        db.session.add(other); db.session.flush()
        other_profile = StudentProfile(user_id=other.id); db.session.add(other_profile); db.session.commit()
        headers = {"Authorization": f"Bearer {create_access_token(identity=other)}"}
    assert client.get(f"/api/assessments/{aid}", headers=headers).status_code == 200
    assert "result" not in client.get(f"/api/assessments/{aid}", headers=headers).json


def test_scores_evidence_gaps_matching_and_recommendations(app, student_profile_id, skill_id):
    with app.app_context():
        skill = Skill.query.get(skill_id)
        db.session.add(StudentSkill(student_id=student_profile_id, skill_id=skill.id, proficiency="ADVANCED"))
        evidence = SkillEvidence(student_id=student_profile_id, skill_id=skill.id, evidence_type="PROJECT", evidence_title="Demo", evidence_strength=1)
        db.session.add(evidence)
        missing = Skill(name="SQL"); db.session.add(missing); db.session.flush()
        role = Role(name="Backend Developer", description="Backend")
        role.requirements.extend([RoleSkillRequirement(skill_id=skill.id, required_proficiency=90, weight=2), RoleSkillRequirement(skill_id=missing.id, required_proficiency=70, weight=1)])
        db.session.add(role); db.session.commit()
        scores = Service.student_scores(student_profile_id)
        python_score = next(item for item in scores if item["skill_id"] == skill.id)
        assert python_score["proficiency_score"] == 75
        assert python_score["evidence_score"] == 25
        assert python_score["overall_score"] == 55
        analysis = Service.analyze_role(student_profile_id, role)
        assert analysis["missing_skills"] == ["SQL"]
        assert next(row for row in analysis["skill_gaps"] if row["skill"] == "SQL")["gap_category"] == "major"
        assert analysis["match_percentage"] == pytest.approx(36.67)
        recs = Service.recommendations(student_profile_id, role.id)
        assert {r["skill"] for r in recs} == {"SQL", "Python"}
        assert next(r for r in recs if r["skill"] == "SQL")["priority"] == "high"


def test_proficiency_and_evidence_boundaries(app, student_profile_id, skill_id):
    with app.app_context():
        skill = Skill.query.get(skill_id)
        student_skill = StudentSkill(student_id=student_profile_id, skill_id=skill.id, proficiency="BEGINNER")
        db.session.add(student_skill); db.session.flush()
        assert Service.proficiency_score(student_skill, []) == 25
        assert Service.proficiency_score(None, [0, 100]) == 50
        assert Service.evidence_score(student_profile_id, skill.id) == 0
        assert Service.student_scores(student_profile_id)[0]["overall_score"] == 15
        project = Project(student_id=student_profile_id, title="Evidence project")
        project.skills.append(skill)
        db.session.add(project); db.session.commit()
        assert Service.evidence_score(student_profile_id, skill.id) == 25
        assert Service.student_scores(student_profile_id)[0]["overall_score"] == 25


def test_only_authorized_users_can_author_assessments(client, auth_headers):
    response = client.post("/api/assessments", headers=auth_headers, json={})
    assert response.status_code == 403
