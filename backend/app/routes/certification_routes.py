"""Certification routes."""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_current_user
from marshmallow import ValidationError

from app.services.certification_service import CertificationService
from app.services.student_service import StudentProfileService
from app.schemas.certification_schema import certification_schema, certification_update_schema, certification_response_schema


certifications_bp = Blueprint("certifications", __name__, url_prefix="/")


@certifications_bp.route("/students/certifications", methods=["GET"])
@jwt_required()
def list_student_certifications():
    """List current student's certifications."""
    current_user = get_current_user()

    if not current_user:
        return jsonify({"error": "User not found", "message": "User account not found"}), 404

    if not current_user.has_role("STUDENT"):
        return jsonify({"error": "Forbidden", "message": "Only students can access student certifications"}), 403

    profile = StudentProfileService.get_profile(current_user.id)
    if not profile:
        return jsonify({"error": "Not found", "message": "Student profile not found"}), 404

    certs = CertificationService.get_student_certifications(profile.id)
    return jsonify([certification_response_schema.dump(cert.to_dict()) for cert in certs]), 200


@certifications_bp.route("/students/certifications", methods=["POST"])
@jwt_required()
def create_student_certification():
    """Create a certification for current student."""
    current_user = get_current_user()

    if not current_user:
        return jsonify({"error": "User not found", "message": "User account not found"}), 404

    if not current_user.has_role("STUDENT"):
        return jsonify({"error": "Forbidden", "message": "Only students can create certifications"}), 403

    profile = StudentProfileService.get_profile(current_user.id)
    if not profile:
        return jsonify({"error": "Not found", "message": "Student profile not found"}), 404

    try:
        data = certification_schema.load(request.get_json() or {})
    except ValidationError as err:
        return jsonify({"error": "Validation error", "messages": err.messages}), 400

    try:
        cert = CertificationService.create_certification(
            student_id=profile.id,
            name=data["name"],
            issuing_organization=data["issuing_organization"],
            issue_date=data["issue_date"],
            expiry_date=data.get("expiry_date"),
            credential_id=data.get("credential_id"),
            credential_url=data.get("credential_url"),
            description=data.get("description")
        )
    except ValueError as e:
        return jsonify({"error": "Certification creation failed", "message": str(e)}), 400

    return jsonify(certification_response_schema.dump(cert.to_dict())), 201


@certifications_bp.route("/students/certifications/<int:cert_id>", methods=["GET"])
@jwt_required()
def get_student_certification(cert_id):
    """Get a specific certification for current student."""
    current_user = get_current_user()

    if not current_user:
        return jsonify({"error": "User not found", "message": "User account not found"}), 404

    if not current_user.has_role("STUDENT"):
        return jsonify({"error": "Forbidden", "message": "Only students can access student certifications"}), 403

    profile = StudentProfileService.get_profile(current_user.id)
    if not profile:
        return jsonify({"error": "Not found", "message": "Student profile not found"}), 404

    cert = CertificationService.get_student_certification(profile.id, cert_id)
    if not cert:
        return jsonify({"error": "Not found", "message": "Certification not found"}), 404

    return jsonify(certification_response_schema.dump(cert.to_dict())), 200


@certifications_bp.route("/students/certifications/<int:cert_id>", methods=["PUT"])
@jwt_required()
def update_student_certification(cert_id):
    """Update current student's certification."""
    current_user = get_current_user()

    if not current_user:
        return jsonify({"error": "User not found", "message": "User account not found"}), 404

    if not current_user.has_role("STUDENT"):
        return jsonify({"error": "Forbidden", "message": "Only students can update certifications"}), 403

    profile = StudentProfileService.get_profile(current_user.id)
    if not profile:
        return jsonify({"error": "Not found", "message": "Student profile not found"}), 404

    try:
        data = certification_update_schema.load(request.get_json() or {})
    except ValidationError as err:
        return jsonify({"error": "Validation error", "messages": err.messages}), 400

    try:
        cert = CertificationService.update_certification(cert_id, profile.id, data)
    except ValueError as e:
        return jsonify({"error": "Certification update failed", "message": str(e)}), 400

    return jsonify(certification_response_schema.dump(cert.to_dict())), 200


@certifications_bp.route("/students/certifications/<int:cert_id>", methods=["DELETE"])
@jwt_required()
def delete_student_certification(cert_id):
    """Delete current student's certification."""
    current_user = get_current_user()

    if not current_user:
        return jsonify({"error": "User not found", "message": "User account not found"}), 404

    if not current_user.has_role("STUDENT"):
        return jsonify({"error": "Forbidden", "message": "Only students can delete certifications"}), 403

    profile = StudentProfileService.get_profile(current_user.id)
    if not profile:
        return jsonify({"error": "Not found", "message": "Student profile not found"}), 404

    success = CertificationService.delete_certification(cert_id, profile.id)
    if not success:
        return jsonify({"error": "Not found", "message": "Certification not found"}), 404

    return jsonify({"message": "Certification deleted successfully"}), 200