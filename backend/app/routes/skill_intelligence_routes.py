"""REST API for assessments and deterministic skill intelligence."""
from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_current_user
from marshmallow import ValidationError
from app.extensions import db
from app.models.assessment import Assessment, AssessmentAttempt
from app.models.role import Role, RoleSkillRequirement
from app.models.skill import Skill
from app.models.student_profile import StudentProfile
from app.schemas.skill_intelligence_schema import AssessmentInputSchema, SubmissionSchema, RoleInputSchema
from app.services.skill_intelligence_service import SkillIntelligenceService as Service

skill_intelligence_bp = Blueprint("skill_intelligence", __name__)
assessment_schema = AssessmentInputSchema()
submission_schema = SubmissionSchema()
role_schema = RoleInputSchema()


def _student():
    user = get_current_user()
    if not user or not user.has_role("STUDENT"):
        return None, (jsonify({"error": "Forbidden", "message": "Only students can access personal skill analysis"}), 403)
    profile = StudentProfile.query.filter_by(user_id=user.id).first()
    if not profile:
        return None, (jsonify({"error": "Not found", "message": "Student profile not found"}), 404)
    return profile, None


def _role_dict(role):
    return {"id": role.id, "name": role.name, "description": role.description, "required_skills": [{"skill_id": r.skill_id, "skill": r.skill.name, "required_proficiency": r.required_proficiency, "weight": r.weight} for r in role.requirements]}


@skill_intelligence_bp.get("/assessments")
@jwt_required()
def list_assessments():
    return jsonify([Service.serialize_assessment(a) for a in Assessment.query.filter_by(is_active=True).all()]), 200


@skill_intelligence_bp.post("/assessments")
@jwt_required()
def create_assessment():
    user = get_current_user()
    if not user or not any(user.has_role(r) for r in ("INSTITUTION", "ACADEMICIAN", "INDUSTRY")):
        return jsonify({"error": "Forbidden", "message": "Assessment authoring is not allowed"}), 403
    try: data = assessment_schema.load(request.get_json() or {})
    except ValidationError as err: return jsonify({"error": "Validation error", "messages": err.messages}), 400
    try:
        assessment = Service.create_assessment(**data, created_by=user.id)
        return jsonify(Service.serialize_assessment(assessment)), 201
    except ValueError as err: db.session.rollback(); return jsonify({"error": "Invalid assessment", "message": str(err)}), 400


@skill_intelligence_bp.get("/assessments/<int:assessment_id>")
@jwt_required()
def get_assessment(assessment_id):
    assessment = Assessment.query.filter_by(id=assessment_id, is_active=True).first()
    if not assessment: return jsonify({"error": "Not found", "message": "Assessment not found"}), 404
    data = Service.serialize_assessment(assessment)
    user = get_current_user()
    if user and user.has_role("STUDENT"):
        profile = StudentProfile.query.filter_by(user_id=user.id).first()
        attempt = AssessmentAttempt.query.filter_by(assessment_id=assessment_id, student_id=profile.id).first() if profile else None
        if attempt: data["result"] = Service.serialize_attempt(attempt)
    return jsonify(data), 200


@skill_intelligence_bp.post("/assessments/<int:assessment_id>/submit")
@jwt_required()
def submit_assessment(assessment_id):
    profile, error = _student()
    if error: return error
    try: data = submission_schema.load(request.get_json() or {})
    except ValidationError as err: return jsonify({"error": "Validation error", "messages": err.messages}), 400
    try: return jsonify(Service.serialize_attempt(Service.submit_assessment(assessment_id, profile.id, data["answers"]))), 201
    except LookupError as err: return jsonify({"error": "Not found", "message": str(err)}), 404
    except ValueError as err: return jsonify({"error": "Invalid submission", "message": str(err)}), 400


@skill_intelligence_bp.get("/skills/scores")
@jwt_required()
def skill_scores():
    profile, error = _student()
    if error: return error
    return jsonify(Service.student_scores(profile.id)), 200


@skill_intelligence_bp.get("/skill-gaps")
@jwt_required()
def skill_gaps():
    profile, error = _student()
    if error: return error
    role_id = request.args.get("role_id", type=int)
    if not role_id: return jsonify({"error": "Validation error", "message": "role_id is required"}), 400
    role = Role.query.get(role_id)
    if not role: return jsonify({"error": "Not found", "message": "Role not found"}), 404
    return jsonify(Service.analyze_role(profile.id, role)), 200


@skill_intelligence_bp.get("/roles")
@jwt_required()
def list_roles(): return jsonify([_role_dict(r) for r in Role.query.order_by(Role.name).all()]), 200


@skill_intelligence_bp.post("/roles")
@jwt_required()
def create_role():
    user = get_current_user()
    if not user or not user.has_role("INSTITUTION"):
        return jsonify({"error": "Forbidden", "message": "Only institution users can manage roles"}), 403
    try: data = role_schema.load(request.get_json() or {})
    except ValidationError as err: return jsonify({"error": "Validation error", "messages": err.messages}), 400
    if Role.query.filter(db.func.lower(Role.name) == data["name"].lower()).first(): return jsonify({"error": "Conflict", "message": "Role already exists"}), 409
    for req in data["requirements"]:
        if not Skill.query.get(req["skill_id"]): return jsonify({"error": "Validation error", "message": f"Skill {req['skill_id']} not found"}), 400
    role = Role(name=data["name"].strip(), description=data.get("description"))
    for req in data["requirements"]: role.requirements.append(RoleSkillRequirement(**req))
    db.session.add(role); db.session.commit()
    return jsonify(_role_dict(role)), 201


@skill_intelligence_bp.post("/roles/seed")
@jwt_required()
def seed_roles():
    user = get_current_user()
    if not user or not user.has_role("INSTITUTION"): return jsonify({"error": "Forbidden", "message": "Only institution users can seed roles"}), 403
    return jsonify([_role_dict(r) for r in Service.seed_roles()]), 200


@skill_intelligence_bp.get("/roles/<int:role_id>")
@jwt_required()
def get_role(role_id):
    role = Role.query.get(role_id)
    if not role: return jsonify({"error": "Not found", "message": "Role not found"}), 404
    return jsonify(_role_dict(role)), 200


@skill_intelligence_bp.get("/roles/<int:role_id>/match")
@jwt_required()
def role_match(role_id):
    profile, error = _student()
    if error: return error
    role = Role.query.get(role_id)
    if not role: return jsonify({"error": "Not found", "message": "Role not found"}), 404
    return jsonify(Service.analyze_role(profile.id, role)), 200


@skill_intelligence_bp.get("/recommendations")
@jwt_required()
def recommendations():
    profile, error = _student()
    if error: return error
    role_id = request.args.get("role_id", type=int)
    try: return jsonify(Service.recommendations(profile.id, role_id)), 200
    except LookupError as err: return jsonify({"error": "Not found", "message": str(err)}), 404
