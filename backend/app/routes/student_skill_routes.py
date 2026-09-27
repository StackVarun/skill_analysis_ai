"""Student skill routes."""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_current_user
from marshmallow import ValidationError

from app.services.student_skill_service import StudentSkillService
from app.services.student_service import StudentProfileService
from app.schemas.student_skill_schema import student_skill_schema, student_skill_update_schema, student_skill_response_schema


student_skills_bp = Blueprint("student_skills", __name__, url_prefix="/")


@student_skills_bp.route("/students/skills", methods=["GET"])
@jwt_required()
def list_student_skills():
    """List current student's skills."""
    current_user = get_current_user()

    if not current_user:
        return jsonify({"error": "User not found", "message": "User account not found"}), 404

    if not current_user.has_role("STUDENT"):
        return jsonify({"error": "Forbidden", "message": "Only students can access student skills"}), 403

    # Get student profile
    profile = StudentProfileService.get_profile(current_user.id)
    if not profile:
        return jsonify({"error": "Not found", "message": "Student profile not found"}), 404

    skills = StudentSkillService.get_student_skills(profile.id)
    return jsonify([student_skill_response_schema.dump(skill.to_dict()) for skill in skills]), 200


@student_skills_bp.route("/students/skills", methods=["POST"])
@jwt_required()
def add_student_skill():
    """Add a skill to current student's profile."""
    current_user = get_current_user()

    if not current_user:
        return jsonify({"error": "User not found", "message": "User account not found"}), 404

    if not current_user.has_role("STUDENT"):
        return jsonify({"error": "Forbidden", "message": "Only students can add skills"}), 403

    profile = StudentProfileService.get_profile(current_user.id)
    if not profile:
        return jsonify({"error": "Not found", "message": "Student profile not found"}), 404

    try:
        data = student_skill_schema.load(request.get_json() or {})
    except ValidationError as err:
        return jsonify({"error": "Validation error", "messages": err.messages}), 400

    try:
        student_skill = StudentSkillService.add_skill(
            student_id=profile.id,
            skill_id=data["skill_id"],
            proficiency=data.get("proficiency", "BEGINNER"),
            years_experience=data.get("years_experience"),
            months_experience=data.get("months_experience"),
            source=data.get("source")
        )
    except ValueError as e:
        return jsonify({"error": "Skill addition failed", "message": str(e)}), 400

    return jsonify(student_skill_response_schema.dump(student_skill.to_dict())), 201


@student_skills_bp.route("/students/skills/<int:skill_id>", methods=["PUT"])
@jwt_required()
def update_student_skill(skill_id):
    """Update current student's skill proficiency."""
    current_user = get_current_user()

    if not current_user:
        return jsonify({"error": "User not found", "message": "User account not found"}), 404

    if not current_user.has_role("STUDENT"):
        return jsonify({"error": "Forbidden", "message": "Only students can update skills"}), 403

    profile = StudentProfileService.get_profile(current_user.id)
    if not profile:
        return jsonify({"error": "Not found", "message": "Student profile not found"}), 404

    try:
        data = student_skill_update_schema.load(request.get_json() or {})
    except ValidationError as err:
        return jsonify({"error": "Validation error", "messages": err.messages}), 400

    try:
        student_skill = StudentSkillService.update_skill(profile.id, skill_id, data)
    except ValueError as e:
        return jsonify({"error": "Skill update failed", "message": str(e)}), 400

    return jsonify(student_skill_response_schema.dump(student_skill.to_dict())), 200


@student_skills_bp.route("/students/skills/<int:skill_id>", methods=["DELETE"])
@jwt_required()
def remove_student_skill(skill_id):
    """Remove a skill from current student's profile."""
    current_user = get_current_user()

    if not current_user:
        return jsonify({"error": "User not found", "message": "User account not found"}), 404

    if not current_user.has_role("STUDENT"):
        return jsonify({"error": "Forbidden", "message": "Only students can remove skills"}), 403

    profile = StudentProfileService.get_profile(current_user.id)
    if not profile:
        return jsonify({"error": "Not found", "message": "Student profile not found"}), 404

    success = StudentSkillService.remove_skill(profile.id, skill_id)
    if not success:
        return jsonify({"error": "Not found", "message": "Student skill not found"}), 404

    return jsonify({"message": "Skill removed successfully"}), 200