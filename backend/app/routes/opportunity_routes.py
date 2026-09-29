from datetime import date
from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_current_user
from marshmallow import Schema, fields, validate, ValidationError
from sqlalchemy.exc import IntegrityError
from app.extensions import db
from app.utils.decorators import roles_required
from app.models.student_profile import StudentProfile
from app.models.skill import Skill
from app.models.opportunity import CompanyProfile, Opportunity, OpportunitySkill, OpportunityApplication
from app.services.opportunity_service import is_open, match_candidate, candidate_record

opportunity_bp = Blueprint('opportunity', __name__)

class CompanyInput(Schema):
    name = fields.Str(required=True, validate=validate.Length(min=2,max=200))
    website = fields.Str(allow_none=True, validate=validate.Length(max=500))
    description = fields.Str(allow_none=True)
    location = fields.Str(allow_none=True, validate=validate.Length(max=200))

class RequirementInput(Schema):
    skill_id = fields.Int(required=True,validate=validate.Range(min=1))
    required_proficiency = fields.Float(required=True,validate=validate.Range(min=0,max=100))
    weight = fields.Float(required=True,validate=validate.Range(min=0.001,max=100))

class PostInput(Schema):
    title = fields.Str(required=True,validate=validate.Length(min=2,max=200))
    description = fields.Str(required=True,validate=validate.Length(min=5))
    kind = fields.Str(required=True,validate=validate.OneOf(['JOB','INTERNSHIP']))
    location = fields.Str(allow_none=True)
    employment_type = fields.Str(allow_none=True)
    eligibility = fields.Str(allow_none=True)
    deadline = fields.Date(allow_none=True)
    stipend = fields.Str(allow_none=True)
    duration = fields.Str(allow_none=True)
    required_skills = fields.List(fields.Nested(RequirementInput),required=True,validate=validate.Length(min=1))

def payload(schema):
    try: return schema.load(request.get_json(silent=True) or {}), None
    except ValidationError as exc: return None, (jsonify({'error':'Validation error','messages':exc.messages}),400)

def company():
    return CompanyProfile.query.filter_by(user_id=get_current_user().id).first()

def own_post(post_id):
    post = Opportunity.query.get(post_id)
    if not post: return None,(jsonify({'error':'Not found'}),404)
    if post.company.user_id != get_current_user().id: return None,(jsonify({'error':'Forbidden'}),403)
    return post,None

@opportunity_bp.route('/industry/company',methods=['GET','PUT'])
@roles_required('INDUSTRY')
def company_profile():
    item = company()
    if request.method == 'GET': return jsonify(item.to_dict() if item else None)
    data,error = payload(CompanyInput())
    if error:return error
    if not item:
        item = CompanyProfile(user_id=get_current_user().id)
        db.session.add(item)
    for key,value in data.items():setattr(item,key,value)
    db.session.commit()
    return jsonify(item.to_dict())

@opportunity_bp.get('/opportunities')
@roles_required('STUDENT','INDUSTRY')
def list_opportunities():
    posts = Opportunity.query.order_by(Opportunity.created_at.desc()).all()
    if get_current_user().has_role('STUDENT'):
        posts = [p for p in posts if is_open(p)]
    else:
        posts = [p for p in posts if p.company.user_id == get_current_user().id]
    return jsonify([p.to_dict() for p in posts])

@opportunity_bp.post('/opportunities')
@roles_required('INDUSTRY')
def create_opportunity():
    firm = company()
    if not firm:return jsonify({'error':'Create a company profile first'}),400
    data,error = payload(PostInput())
    if error:return error
    required = data.pop('required_skills')
    if len({r['skill_id'] for r in required}) != len(required):return jsonify({'error':'Duplicate required skill'}),400
    if any(not Skill.query.get(r['skill_id']) for r in required):return jsonify({'error':'Unknown skill'}),400
    if data.get('deadline') and data['deadline'] < date.today():return jsonify({'error':'Deadline is in the past'}),400
    post = Opportunity(company_id=firm.id,**data)
    post.requirements = [OpportunitySkill(**r) for r in required]
    db.session.add(post);db.session.commit()
    return jsonify(post.to_dict()),201

@opportunity_bp.route('/opportunities/<int:post_id>',methods=['GET','PUT','DELETE'])
@roles_required('STUDENT','INDUSTRY')
def opportunity_detail(post_id):
    if request.method == 'GET':
        post = Opportunity.query.get(post_id)
        if not post:return jsonify({'error':'Not found'}),404
        if get_current_user().has_role('STUDENT') and not is_open(post):return jsonify({'error':'Not found'}),404
        if get_current_user().has_role('INDUSTRY') and post.company.user_id != get_current_user().id:return jsonify({'error':'Forbidden'}),403
        return jsonify(post.to_dict())
    if not get_current_user().has_role('INDUSTRY'):return jsonify({'error':'Forbidden'}),403
    post,error = own_post(post_id)
    if error:return error
    if request.method == 'DELETE':
        post.is_active = False;db.session.commit();return '',204
    data,error = payload(PostInput())
    if error:return error
    required = data.pop('required_skills')
    if len({r['skill_id'] for r in required}) != len(required) or any(not Skill.query.get(r['skill_id']) for r in required):return jsonify({'error':'Invalid required skills'}),400
    if data.get('deadline') and data['deadline'] < date.today():return jsonify({'error':'Deadline is in the past'}),400
    for key,value in data.items():setattr(post,key,value)
    post.requirements = [OpportunitySkill(**r) for r in required]
    db.session.commit();return jsonify(post.to_dict())

@opportunity_bp.post('/opportunities/<int:post_id>/apply')
@roles_required('STUDENT')
def apply(post_id):
    post = Opportunity.query.get(post_id)
    if not post or not is_open(post):return jsonify({'error':'Opportunity unavailable'}),404
    student = StudentProfile.query.filter_by(user_id=get_current_user().id).first()
    if not student:return jsonify({'error':'Student profile required'}),400
    if OpportunityApplication.query.filter_by(opportunity_id=post_id,student_id=student.id).first():return jsonify({'error':'Already applied'}),409
    application = OpportunityApplication(opportunity_id=post_id,student_id=student.id)
    db.session.add(application);db.session.commit();return jsonify(application.to_dict()),201

@opportunity_bp.get('/applications/mine')
@roles_required('STUDENT')
def my_applications():
    student = StudentProfile.query.filter_by(user_id=get_current_user().id).first()
    if not student:return jsonify([])
    return jsonify([{**a.to_dict(),'opportunity':a.opportunity.to_dict()} for a in OpportunityApplication.query.filter_by(student_id=student.id).all()])

@opportunity_bp.get('/opportunities/<int:post_id>/applications')
@roles_required('INDUSTRY')
def applications(post_id):
    post,error = own_post(post_id)
    if error:return error
    return jsonify([candidate_record(a) for a in post.applications])

@opportunity_bp.post('/applications/<int:application_id>/shortlist')
@roles_required('INDUSTRY')
def shortlist(application_id):
    application = OpportunityApplication.query.get(application_id)
    if not application:return jsonify({'error':'Not found'}),404
    if application.opportunity.company.user_id != get_current_user().id:return jsonify({'error':'Forbidden'}),403
    application.status = 'SHORTLISTED';db.session.commit()
    return jsonify(candidate_record(application))

@opportunity_bp.get('/industry/summary')
@roles_required('INDUSTRY')
def summary():
    firm = company()
    posts = Opportunity.query.filter_by(company_id=firm.id).all() if firm else []
    return jsonify({'jobs':sum(p.kind=='JOB' and is_open(p) for p in posts),
                    'internships':sum(p.kind=='INTERNSHIP' and is_open(p) for p in posts),
                    'applications':sum(len(p.applications) for p in posts),
                    'shortlisted':sum(a.status=='SHORTLISTED' for p in posts for a in p.applications)})
