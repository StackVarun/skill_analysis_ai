"""Experience routes."""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_current_user
from marshmallow import ValidationError

from app.services.experience_service import ExperienceService
from app.services.student_service import StudentProfileService
from app.schemas.experience_schema import experience_schema, experience_update_schema, experience_response_schema


experiences_bp = Blueprint("experiences", __name__, url_prefix="/")


@experiences_bp.route("/students/experience", methods=["GET"])
@jwt_required()
def list_student_experiences():
    """List current student's experiences."""
    current_user = get_current_user()

    if not current_user:
        return jsonify({"error": "User not found", "message": "User account not found"}), 404

    if not current_user.has_role("STUDENT"):
        return jsonify({"error": "Forbidden", "message": "Only students can access student experiences"}), 403

    profile = StudentProfileService.get_profile(current_user.id)
    if not profile:
        return jsonify({"error": "Not found", "message": "Student profile not found"}), 404

    experiences = ExperienceService.get_student_experiences(profile.id)
    return jsonify([experience_response_schema.dump(exp.to_dict()) for exp in experiences]), 200


@experiences_bp.route("/students/experience", methods=["POST"])
@jwt_required()
def create_student_experience():
    """Create an experience for current student."""
    current_user = get_current_user()

    if not current_user:
        return jsonify({"error": "User not found", "message": "User account not found"}), 404

    if not current_user.has_role("STUDENT"):
        return jsonify({"error": "Forbidden", "message": "Only students can create experiences"}), 403

    profile = StudentProfileService.get_profile(current_user.id)
    if not profile:
        return jsonify({"error": "Not found", "message": "Student profile not found"}), 404

    try:
        data = experience_schema.load(request.get_json() or {})
    except ValidationError as err:
        return jsonify({"error": "Validation error", "messages": err.messages}), 400

    try:
        exp = ExperienceService.create_experience(
            student_id=profile.id,
            organization=data["organization"],
            job_title=data["job_title"],
            start_date=data["start_date"],
            employment_type=data.get("employment_type", "FULL_TIME"),
            location=data.get("location"),
            end_date=data.get("end_date"),
            description=data.get("description"),
            skill_ids=data.get("skill_ids", [])
        )
    except ValueError as e:
        return jsonify({"error": "Experience creation failed", "message": str(e)}), 400

    return jsonify(experience_response_schema.dump(exp.to_dict())), 201


@experiences_bp.route("/students/experience/<int:exp_id>", methods=["GET"])
@jwt_required()
def get_student_experience(exp_id):
    """Get a specific experience for current student."""
    current_user = get_current_user()

    if not current_user:
        return jsonify({"error": "User not found", "message": "User account not found"}), 404

    if not current_user.has_role("STUDENT"):
        return jsonify({"error": "Forbidden", "message": "Only students can access student experiences"}), 403

    profile = StudentProfileService.get_profile(current_user.id)
    if not profile:
        return jsonify({"error": "Not found", "message": "Student profile not found"}), 404

    exp = ExperienceService.get_student_experience(profile.id, exp_id)
    if not exp:
        return jsonify({"error": "Not found", "message": "Experience not found"}), 404

    return jsonify(experience_response_schema.dump(exp.to_dict())), 200


@experiences_bp.route("/students/experience/<int:exp_id>", methods=["PUT"])
@jwt_required()
def update_student_experience(exp_id):
    """Update current student's experience."""
    current_user = get_current_user()

    if not current_user:
        return jsonify({"error": "User not found", "message": "User account not found"}), 404

    if not current_user.has_role("STUDENT"):
        return jsonify({"error": "Forbidden", "message": "Only students can update experiences"}), 403

    profile = StudentProfileService.get_profile(current_user.id)
    if not profile:
        return jsonify({"error": "Not found", "message": "Student profile not found"}), 404

    try:
        data = experience_update_schema.load(request.get_json() or {})
    except ValidationError as err:
        return jsonify({"error": "Validation error", "messages": err.messages}), 400

    try:
        exp = ExperienceService.update_experience(exp_id, profile.id, data)
    except ValueError as e:
        return jsonify({"error": "Experience update failed", "message": str(e)}), 400

    return jsonify(experience_response_schema.dump(exp.to_dict())), 200


@experiences_bp.route("/students/experience/<int:exp_id>", methods=["DELETE"])
@jwt_required()
def delete_student_experience(exp_id):
    """Delete current student's experience."""
    current_user = get_current_user()

    if not current_user:
        return jsonify({"error": "User not found", "message": "User account not found"}), 404

    if not current_user.has_role("STUDENT"):
        return jsonify({"error": "Forbidden", "message": "Only students can delete experiences"}), 403

    profile = StudentProfileService.get_profile(current_user.id)
    if not profile:
        return jsonify({"error": "Not found", "message": "Student profile not found"}), 404

    success = ExperienceService.delete_experience(exp_id, profile.id)
    if not success:
        return jsonify({"error": "Not found", "message": "Experience not found"}), 404

    return jsonify({"message": "Experience deleted successfully"}), 200