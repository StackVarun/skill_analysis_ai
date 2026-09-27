"""Skill routes."""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_current_user
from marshmallow import ValidationError

from app.services.skill_service import SkillService
from app.schemas.skill_schema import skill_schema, skill_response_schema
from app.models.enums import UserRole
from app.utils.decorators import roles_required


skills_bp = Blueprint("skills", __name__, url_prefix="/")


@skills_bp.route("/skills", methods=["GET"])
def list_skills():
    """List all skills with optional filtering."""
    category = request.args.get("category")
    search = request.args.get("search")

    skills = SkillService.get_all_skills(category=category, search=search)
    return jsonify([skill_response_schema.dump(skill.to_dict()) for skill in skills]), 200


@skills_bp.route("/skills/<int:skill_id>", methods=["GET"])
def get_skill(skill_id):
    """Get a skill by ID."""
    skill = SkillService.get_skill_by_id(skill_id)
    if not skill:
        return jsonify({"error": "Not found", "message": "Skill not found"}), 404

    return jsonify(skill_response_schema.dump(skill.to_dict())), 200


@skills_bp.route("/skills", methods=["POST"])
@jwt_required()
@roles_required("INDUSTRY", "INSTITUTION", "ACADEMICIAN")
def create_skill():
    """Create a new skill (restricted to industry, institution, academician roles)."""
    current_user = get_current_user()

    if not current_user:
        return jsonify({"error": "User not found", "message": "User account not found"}), 404

    try:
        data = skill_schema.load(request.get_json() or {})
    except ValidationError as err:
        return jsonify({"error": "Validation error", "messages": err.messages}), 400

    try:
        skill = SkillService.create_skill(
            name=data["name"],
            category=data.get("category"),
            description=data.get("description")
        )
    except ValueError as e:
        return jsonify({"error": "Skill creation failed", "message": str(e)}), 400

    return jsonify(skill_response_schema.dump(skill.to_dict())), 201