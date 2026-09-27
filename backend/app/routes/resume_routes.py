"""Resume routes."""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_current_user
from werkzeug.utils import secure_filename

from app.services.resume_service import ResumeService
from app.services.student_service import StudentProfileService
from app.schemas.resume_schema import resume_response_schema


resumes_bp = Blueprint("resumes", __name__, url_prefix="/")


@resumes_bp.route("/students/resume", methods=["GET"])
@jwt_required()
def list_student_resumes():
    """List current student's resumes."""
    current_user = get_current_user()

    if not current_user:
        return jsonify({"error": "User not found", "message": "User account not found"}), 404

    if not current_user.has_role("STUDENT"):
        return jsonify({"error": "Forbidden", "message": "Only students can access resumes"}), 403

    profile = StudentProfileService.get_profile(current_user.id)
    if not profile:
        return jsonify({"error": "Not found", "message": "Student profile not found"}), 404

    resumes = ResumeService.get_student_resumes(profile.id)
    return jsonify([resume_response_schema.dump(r.to_dict()) for r in resumes]), 200


@resumes_bp.route("/students/resume", methods=["POST"])
@jwt_required()
def upload_student_resume():
    """Upload a resume for current student."""
    current_user = get_current_user()

    if not current_user:
        return jsonify({"error": "User not found", "message": "User account not found"}), 404

    if not current_user.has_role("STUDENT"):
        return jsonify({"error": "Forbidden", "message": "Only students can upload resumes"}), 403

    profile = StudentProfileService.get_profile(current_user.id)
    if not profile:
        return jsonify({"error": "Not found", "message": "Student profile not found"}), 404

    if "file" not in request.files:
        return jsonify({"error": "No file provided", "message": "Please provide a resume file"}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "No file selected", "message": "Please select a file to upload"}), 400

    try:
        resume = ResumeService.create_resume(profile.id, file)
    except ValueError as e:
        return jsonify({"error": "Upload failed", "message": str(e)}), 400

    return jsonify(resume_response_schema.dump(resume.to_dict())), 201


@resumes_bp.route("/students/resume/<int:resume_id>", methods=["GET"])
@jwt_required()
def get_student_resume(resume_id):
    """Get a specific resume for current student."""
    current_user = get_current_user()

    if not current_user:
        return jsonify({"error": "User not found", "message": "User account not found"}), 404

    if not current_user.has_role("STUDENT"):
        return jsonify({"error": "Forbidden", "message": "Only students can access resumes"}), 403

    profile = StudentProfileService.get_profile(current_user.id)
    if not profile:
        return jsonify({"error": "Not found", "message": "Student profile not found"}), 404

    resume = ResumeService.get_student_resume(profile.id, resume_id)
    if not resume:
        return jsonify({"error": "Not found", "message": "Resume not found"}), 404

    return jsonify(resume_response_schema.dump(resume.to_dict())), 200


@resumes_bp.route("/students/resume/<int:resume_id>", methods=["DELETE"])
@jwt_required()
def delete_student_resume(resume_id):
    """Delete current student's resume."""
    current_user = get_current_user()

    if not current_user:
        return jsonify({"error": "User not found", "message": "User account not found"}), 404

    if not current_user.has_role("STUDENT"):
        return jsonify({"error": "Forbidden", "message": "Only students can delete resumes"}), 403

    profile = StudentProfileService.get_profile(current_user.id)
    if not profile:
        return jsonify({"error": "Not found", "message": "Student profile not found"}), 404

    success = ResumeService.delete_resume(resume_id, profile.id)
    if not success:
        return jsonify({"error": "Not found", "message": "Resume not found"}), 404

    return jsonify({"message": "Resume deleted successfully"}), 200