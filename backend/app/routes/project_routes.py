"""Project routes."""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_current_user
from marshmallow import ValidationError

from app.services.project_service import ProjectService
from app.services.student_service import StudentProfileService
from app.schemas.project_schema import project_schema, project_update_schema, project_response_schema


projects_bp = Blueprint("projects", __name__, url_prefix="/")


@projects_bp.route("/students/projects", methods=["GET"])
@jwt_required()
def list_student_projects():
    """List current student's projects."""
    current_user = get_current_user()

    if not current_user:
        return jsonify({"error": "User not found", "message": "User account not found"}), 404

    if not current_user.has_role("STUDENT"):
        return jsonify({"error": "Forbidden", "message": "Only students can access student projects"}), 403

    profile = StudentProfileService.get_profile(current_user.id)
    if not profile:
        return jsonify({"error": "Not found", "message": "Student profile not found"}), 404

    projects = ProjectService.get_student_projects(profile.id)
    return jsonify([project_response_schema.dump(project.to_dict()) for project in projects]), 200


@projects_bp.route("/students/projects", methods=["POST"])
@jwt_required()
def create_student_project():
    """Create a project for current student."""
    current_user = get_current_user()

    if not current_user:
        return jsonify({"error": "User not found", "message": "User account not found"}), 404

    if not current_user.has_role("STUDENT"):
        return jsonify({"error": "Forbidden", "message": "Only students can create projects"}), 403

    profile = StudentProfileService.get_profile(current_user.id)
    if not profile:
        return jsonify({"error": "Not found", "message": "Student profile not found"}), 404

    try:
        data = project_schema.load(request.get_json() or {})
    except ValidationError as err:
        return jsonify({"error": "Validation error", "messages": err.messages}), 400

    try:
        project = ProjectService.create_project(
            student_id=profile.id,
            title=data["title"],
            description=data.get("description"),
            technologies=data.get("technologies"),
            project_url=data.get("project_url"),
            github_url=data.get("github_url"),
            start_date=data.get("start_date"),
            end_date=data.get("end_date"),
            role=data.get("role"),
            skill_ids=data.get("skill_ids", []),
            completion_status=data.get("completion_status", "COMPLETED")
        )
    except ValueError as e:
        return jsonify({"error": "Project creation failed", "message": str(e)}), 400

    return jsonify(project_response_schema.dump(project.to_dict())), 201


@projects_bp.route("/students/projects/<int:project_id>", methods=["GET"])
@jwt_required()
def get_student_project(project_id):
    """Get a specific project for current student."""
    current_user = get_current_user()

    if not current_user:
        return jsonify({"error": "User not found", "message": "User account not found"}), 404

    if not current_user.has_role("STUDENT"):
        return jsonify({"error": "Forbidden", "message": "Only students can access student projects"}), 403

    profile = StudentProfileService.get_profile(current_user.id)
    if not profile:
        return jsonify({"error": "Not found", "message": "Student profile not found"}), 404

    project = ProjectService.get_student_project(profile.id, project_id)
    if not project:
        return jsonify({"error": "Not found", "message": "Project not found"}), 404

    return jsonify(project_response_schema.dump(project.to_dict())), 200


@projects_bp.route("/students/projects/<int:project_id>", methods=["PUT"])
@jwt_required()
def update_student_project(project_id):
    """Update current student's project."""
    current_user = get_current_user()

    if not current_user:
        return jsonify({"error": "User not found", "message": "User account not found"}), 404

    if not current_user.has_role("STUDENT"):
        return jsonify({"error": "Forbidden", "message": "Only students can update projects"}), 403

    profile = StudentProfileService.get_profile(current_user.id)
    if not profile:
        return jsonify({"error": "Not found", "message": "Student profile not found"}), 404

    try:
        data = project_update_schema.load(request.get_json() or {})
    except ValidationError as err:
        return jsonify({"error": "Validation error", "messages": err.messages}), 400

    try:
        project = ProjectService.update_project(project_id, profile.id, data)
    except ValueError as e:
        return jsonify({"error": "Project update failed", "message": str(e)}), 400

    return jsonify(project_response_schema.dump(project.to_dict())), 200


@projects_bp.route("/students/projects/<int:project_id>", methods=["DELETE"])
@jwt_required()
def delete_student_project(project_id):
    """Delete current student's project."""
    current_user = get_current_user()

    if not current_user:
        return jsonify({"error": "User not found", "message": "User account not found"}), 404

    if not current_user.has_role("STUDENT"):
        return jsonify({"error": "Forbidden", "message": "Only students can delete projects"}), 403

    profile = StudentProfileService.get_profile(current_user.id)
    if not profile:
        return jsonify({"error": "Not found", "message": "Student profile not found"}), 404

    success = ProjectService.delete_project(project_id, profile.id)
    if not success:
        return jsonify({"error": "Not found", "message": "Project not found"}), 404

    return jsonify({"message": "Project deleted successfully"}), 200