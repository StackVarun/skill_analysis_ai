"""Internship routes."""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_current_user
from marshmallow import ValidationError

from app.services.internship_service import InternshipService
from app.services.student_service import StudentProfileService
from app.schemas.internship_schema import internship_schema, internship_update_schema, internship_response_schema


internships_bp = Blueprint("internships", __name__, url_prefix="/")


@internships_bp.route("/students/internships", methods=["GET"])
@jwt_required()
def list_student_internships():
    """List current student's internships."""
    current_user = get_current_user()

    if not current_user:
        return jsonify({"error": "User not found", "message": "User account not found"}), 404

    if not current_user.has_role("STUDENT"):
        return jsonify({"error": "Forbidden", "message": "Only students can access student internships"}), 403

    profile = StudentProfileService.get_profile(current_user.id)
    if not profile:
        return jsonify({"error": "Not found", "message": "Student profile not found"}), 404

    internships = InternshipService.get_student_internships(profile.id)
    return jsonify([internship_response_schema.dump(i.to_dict()) for i in internships]), 200


@internships_bp.route("/students/internships", methods=["POST"])
@jwt_required()
def create_student_internship():
    """Create an internship for current student."""
    current_user = get_current_user()

    if not current_user:
        return jsonify({"error": "User not found", "message": "User account not found"}), 404

    if not current_user.has_role("STUDENT"):
        return jsonify({"error": "Forbidden", "message": "Only students can create internships"}), 403

    profile = StudentProfileService.get_profile(current_user.id)
    if not profile:
        return jsonify({"error": "Not found", "message": "Student profile not found"}), 404

    try:
        data = internship_schema.load(request.get_json() or {})
    except ValidationError as err:
        return jsonify({"error": "Validation error", "messages": err.messages}), 400

    try:
        internship = InternshipService.create_internship(
            student_id=profile.id,
            organization=data["organization"],
            role=data["role"],
            start_date=data["start_date"],
            end_date=data.get("end_date"),
            description=data.get("description"),
            certificate_url=data.get("certificate_url"),
            internship_type=data.get("internship_type", "SUMMER"),
            status=data.get("status", "COMPLETED"),
            skill_ids=data.get("skill_ids", [])
        )
    except ValueError as e:
        return jsonify({"error": "Internship creation failed", "message": str(e)}), 400

    return jsonify(internship_response_schema.dump(internship.to_dict())), 201


@internships_bp.route("/students/internships/<int:internship_id>", methods=["GET"])
@jwt_required()
def get_student_internship(internship_id):
    """Get a specific internship for current student."""
    current_user = get_current_user()

    if not current_user:
        return jsonify({"error": "User not found", "message": "User account not found"}), 404

    if not current_user.has_role("STUDENT"):
        return jsonify({"error": "Forbidden", "message": "Only students can access student internships"}), 403

    profile = StudentProfileService.get_profile(current_user.id)
    if not profile:
        return jsonify({"error": "Not found", "message": "Student profile not found"}), 404

    internship = InternshipService.get_student_internship(profile.id, internship_id)
    if not internship:
        return jsonify({"error": "Not found", "message": "Internship not found"}), 404

    return jsonify(internship_response_schema.dump(internship.to_dict())), 200


@internships_bp.route("/students/internships/<int:internship_id>", methods=["PUT"])
@jwt_required()
def update_student_internship(internship_id):
    """Update current student's internship."""
    current_user = get_current_user()

    if not current_user:
        return jsonify({"error": "User not found", "message": "User account not found"}), 404

    if not current_user.has_role("STUDENT"):
        return jsonify({"error": "Forbidden", "message": "Only students can update internships"}), 403

    profile = StudentProfileService.get_profile(current_user.id)
    if not profile:
        return jsonify({"error": "Not found", "message": "Student profile not found"}), 404

    try:
        data = internship_update_schema.load(request.get_json() or {})
    except ValidationError as err:
        return jsonify({"error": "Validation error", "messages": err.messages}), 400

    try:
        internship = InternshipService.update_internship(internship_id, profile.id, data)
    except ValueError as e:
        return jsonify({"error": "Internship update failed", "message": str(e)}), 400

    return jsonify(internship_response_schema.dump(internship.to_dict())), 200


@internships_bp.route("/students/internships/<int:internship_id>", methods=["DELETE"])
@jwt_required()
def delete_student_internship(internship_id):
    """Delete current student's internship."""
    current_user = get_current_user()

    if not current_user:
        return jsonify({"error": "User not found", "message": "User account not found"}), 404

    if not current_user.has_role("STUDENT"):
        return jsonify({"error": "Forbidden", "message": "Only students can delete internships"}), 403

    profile = StudentProfileService.get_profile(current_user.id)
    if not profile:
        return jsonify({"error": "Not found", "message": "Student profile not found"}), 404

    success = InternshipService.delete_internship(internship_id, profile.id)
    if not success:
        return jsonify({"error": "Not found", "message": "Internship not found"}), 404

    return jsonify({"message": "Internship deleted successfully"}), 200