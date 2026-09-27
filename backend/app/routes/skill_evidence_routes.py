"""Skill evidence routes."""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_current_user
from marshmallow import ValidationError

from app.services.skill_evidence_service import SkillEvidenceService
from app.services.student_service import StudentProfileService
from app.schemas.skill_evidence_schema import skill_evidence_schema, skill_evidence_update_schema, skill_evidence_response_schema


skill_evidence_bp = Blueprint("skill_evidence", __name__, url_prefix="/")


@skill_evidence_bp.route("/students/skill-evidence", methods=["GET"])
@jwt_required()
def list_student_skill_evidence():
    """List current student's skill evidence."""
    current_user = get_current_user()

    if not current_user:
        return jsonify({"error": "User not found", "message": "User account not found"}), 404

    if not current_user.has_role("STUDENT"):
        return jsonify({"error": "Forbidden", "message": "Only students can access skill evidence"}), 403

    profile = StudentProfileService.get_profile(current_user.id)
    if not profile:
        return jsonify({"error": "Not found", "message": "Student profile not found"}), 404

    evidence = SkillEvidenceService.get_student_evidence(profile.id)
    return jsonify([skill_evidence_response_schema.dump(e.to_dict()) for e in evidence]), 200


@skill_evidence_bp.route("/students/skill-evidence", methods=["POST"])
@jwt_required()
def create_student_skill_evidence():
    """Create skill evidence for current student."""
    current_user = get_current_user()

    if not current_user:
        return jsonify({"error": "User not found", "message": "User account not found"}), 404

    if not current_user.has_role("STUDENT"):
        return jsonify({"error": "Forbidden", "message": "Only students can create skill evidence"}), 403

    profile = StudentProfileService.get_profile(current_user.id)
    if not profile:
        return jsonify({"error": "Not found", "message": "Student profile not found"}), 404

    try:
        data = skill_evidence_schema.load(request.get_json() or {})
    except ValidationError as err:
        return jsonify({"error": "Validation error", "messages": err.messages}), 400

    try:
        evidence = SkillEvidenceService.create_evidence(
            student_id=profile.id,
            skill_id=data["skill_id"],
            evidence_type=data["evidence_type"],
            evidence_title=data["evidence_title"],
            description=data.get("description"),
            source_url=data.get("source_url"),
            project_id=data.get("project_id"),
            certification_id=data.get("certification_id"),
            experience_id=data.get("experience_id"),
            internship_id=data.get("internship_id"),
            verification_status=data.get("verification_status", "SELF_REPORTED"),
            evidence_strength=data.get("evidence_strength")
        )
    except ValueError as e:
        return jsonify({"error": "Evidence creation failed", "message": str(e)}), 400

    return jsonify(skill_evidence_response_schema.dump(evidence.to_dict())), 201


@skill_evidence_bp.route("/students/skill-evidence/<int:evidence_id>", methods=["GET"])
@jwt_required()
def get_student_skill_evidence(evidence_id):
    """Get a specific skill evidence for current student."""
    current_user = get_current_user()

    if not current_user:
        return jsonify({"error": "User not found", "message": "User account not found"}), 404

    if not current_user.has_role("STUDENT"):
        return jsonify({"error": "Forbidden", "message": "Only students can access skill evidence"}), 403

    profile = StudentProfileService.get_profile(current_user.id)
    if not profile:
        return jsonify({"error": "Not found", "message": "Student profile not found"}), 404

    evidence = SkillEvidenceService.get_student_evidence_by_id(profile.id, evidence_id)
    if not evidence:
        return jsonify({"error": "Not found", "message": "Skill evidence not found"}), 404

    return jsonify(skill_evidence_response_schema.dump(evidence.to_dict())), 200


@skill_evidence_bp.route("/students/skill-evidence/<int:evidence_id>", methods=["PUT"])
@jwt_required()
def update_student_skill_evidence(evidence_id):
    """Update current student's skill evidence."""
    current_user = get_current_user()

    if not current_user:
        return jsonify({"error": "User not found", "message": "User account not found"}), 404

    if not current_user.has_role("STUDENT"):
        return jsonify({"error": "Forbidden", "message": "Only students can update skill evidence"}), 403

    profile = StudentProfileService.get_profile(current_user.id)
    if not profile:
        return jsonify({"error": "Not found", "message": "Student profile not found"}), 404

    try:
        data = skill_evidence_update_schema.load(request.get_json() or {})
    except ValidationError as err:
        return jsonify({"error": "Validation error", "messages": err.messages}), 400

    try:
        evidence = SkillEvidenceService.update_evidence(evidence_id, profile.id, data)
    except ValueError as e:
        return jsonify({"error": "Evidence update failed", "message": str(e)}), 400

    return jsonify(skill_evidence_response_schema.dump(evidence.to_dict())), 200


@skill_evidence_bp.route("/students/skill-evidence/<int:evidence_id>", methods=["DELETE"])
@jwt_required()
def delete_student_skill_evidence(evidence_id):
    """Delete current student's skill evidence."""
    current_user = get_current_user()

    if not current_user:
        return jsonify({"error": "User not found", "message": "User account not found"}), 404

    if not current_user.has_role("STUDENT"):
        return jsonify({"error": "Forbidden", "message": "Only students can delete skill evidence"}), 403

    profile = StudentProfileService.get_profile(current_user.id)
    if not profile:
        return jsonify({"error": "Not found", "message": "Student profile not found"}), 404

    success = SkillEvidenceService.delete_evidence(evidence_id, profile.id)
    if not success:
        return jsonify({"error": "Not found", "message": "Skill evidence not found"}), 404

    return jsonify({"message": "Skill evidence deleted successfully"}), 200