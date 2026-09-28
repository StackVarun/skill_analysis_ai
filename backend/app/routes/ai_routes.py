"""Authenticated API for optional local AI assistance."""
from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_current_user, jwt_required
from marshmallow import ValidationError

from app.models.resume import Resume
from app.models.role import Role
from app.models.student_profile import StudentProfile
from app.schemas.ai_schema import (GapExplanationInputSchema, ResumeExtractionInputSchema,
                                   RoadmapInputSchema, SkillNormalizationInputSchema)
from app.services.local_ai_service import LocalAIService
from app.services.skill_intelligence_service import SkillIntelligenceService

ai_bp = Blueprint("local_ai", __name__)
ai_service = LocalAIService()
resume_input = ResumeExtractionInputSchema()
normalization_input = SkillNormalizationInputSchema()
gap_input = GapExplanationInputSchema()
roadmap_input = RoadmapInputSchema()


def _student():
    user = get_current_user()
    if not user or not user.has_role("STUDENT"):
        return None, (jsonify({"error": "Forbidden", "message": "Only students can use personal AI assistance"}), 403)
    profile = StudentProfile.query.filter_by(user_id=user.id).first()
    if not profile:
        return None, (jsonify({"error": "Not found", "message": "Student profile not found"}), 404)
    return profile, None


def _load(schema):
    try:
        return schema.load(request.get_json() or {}), None
    except ValidationError as error:
        return None, (jsonify({"error": "Validation error", "messages": error.messages}), 400)


@ai_bp.post("/ai/resume-skills/extract")
@jwt_required()
def extract_resume_skills():
    profile, error = _student()
    if error: return error
    data, error = _load(resume_input)
    if error: return error
    resume = Resume.query.filter_by(id=data["resume_id"], student_id=profile.id).first()
    if not resume: return jsonify({"error": "Not found", "message": "Resume not found"}), 404
    try: return jsonify(ai_service.extract_resume_skills(profile.id, resume)), 200
    except ValueError as err: return jsonify({"error": "Invalid resume", "message": str(err)}), 400


@ai_bp.post("/ai/skills/normalize")
@jwt_required()
def normalize_skill():
    _, error = _student()
    if error: return error
    data, error = _load(normalization_input)
    if error: return error
    return jsonify(ai_service.normalize_skill(data["variant"].strip())), 200


@ai_bp.post("/ai/skill-gaps/explain")
@jwt_required()
def explain_skill_gaps():
    profile, error = _student()
    if error: return error
    data, error = _load(gap_input)
    if error: return error
    role = Role.query.get(data["role_id"])
    if not role: return jsonify({"error": "Not found", "message": "Role not found"}), 404
    deterministic = SkillIntelligenceService.analyze_role(profile.id, role)
    return jsonify(ai_service.explain_gaps(deterministic)), 200


@ai_bp.post("/ai/learning-roadmap")
@jwt_required()
def learning_roadmap():
    profile, error = _student()
    if error: return error
    data, error = _load(roadmap_input)
    if error: return error
    role = Role.query.get(data["role_id"])
    if not role: return jsonify({"error": "Not found", "message": "Role not found"}), 404
    deterministic = SkillIntelligenceService.analyze_role(profile.id, role)
    return jsonify(ai_service.learning_roadmap(profile.id, role, deterministic)), 200
