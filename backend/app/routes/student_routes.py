"""Student profile routes."""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_current_user
from marshmallow import ValidationError

from app.services.student_service import StudentProfileService
from app.schemas.student_schema import student_profile_schema, student_profile_response_schema


student_bp = Blueprint("students", __name__, url_prefix="/students")


@student_bp.route("/profile", methods=["GET"])
@jwt_required()
def get_profile():
    """Get current student's profile."""
    current_user = get_current_user()

    if not current_user:
        return jsonify({"error": "User not found", "message": "User account not found"}), 404

    if not current_user.has_role("STUDENT"):
        return jsonify({"error": "Forbidden", "message": "Only students can access student profile"}), 403

    profile = StudentProfileService.get_profile(current_user.id)

    if not profile:
        return jsonify({"error": "Not found", "message": "Student profile not found"}), 404

    return jsonify(student_profile_response_schema.dump(profile.to_dict())), 200


@student_bp.route("/profile", methods=["PUT"])
@jwt_required()
def update_profile():
    """Create or update current student's profile."""
    current_user = get_current_user()

    if not current_user:
        return jsonify({"error": "User not found", "message": "User account not found"}), 404

    if not current_user.has_role("STUDENT"):
        return jsonify({"error": "Forbidden", "message": "Only students can update student profile"}), 403

    try:
        data = student_profile_schema.load(request.get_json() or {})
    except ValidationError as err:
        return jsonify({"error": "Validation error", "messages": err.messages}), 400

    try:
        profile = StudentProfileService.create_or_update_profile(current_user.id, data)
    except ValueError as e:
        return jsonify({"error": "Profile update failed", "message": str(e)}), 400

    return jsonify(student_profile_response_schema.dump(profile.to_dict())), 200