from datetime import date
from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_current_user
from marshmallow import Schema, fields, validate, ValidationError
from app.extensions import db
from app.utils.decorators import roles_required
from app.models.faculty import FacultyProfile, FacultyOpportunity, FacultyApplication
from app.models.user import User
faculty_bp = Blueprint('faculty',__name__)
KINDS = ['FACULTY_INTERNSHIP','FDP','INDUSTRIAL_TRAINING','CONSULTANCY','RESEARCH_COLLABORATION']
class ProfileInput(Schema):
    institution = fields.Str(required=True,validate=validate.Length(min=2,max=200))
    department = fields.Str(allow_none=True)
    designation = fields.Str(allow_none=True)
    interests = fields.Str(allow_none=True)
class FacultyInput(Schema):
    title = fields.Str(required=True,validate=validate.Length(min=2,max=200))
    kind = fields.Str(required=True,validate=validate.OneOf(KINDS))
    description = fields.Str(required=True,validate=validate.Length(min=5))
    organization = fields.Str(allow_none=True)
    deadline = fields.Date(allow_none=True)
def parse(schema):
    try:return schema.load(request.get_json(silent=True) or {}),None
    except ValidationError as e:return None,(jsonify({'error':'Validation error','messages':e.messages}),400)
@faculty_bp.route('/faculty/profile',methods=['GET','PUT'])
@roles_required('ACADEMICIAN')
def profile():
    item = FacultyProfile.query.filter_by(user_id=get_current_user().id).first()
    if request.method=='GET':return jsonify(item.to_dict() if item else None)
    data,error=parse(ProfileInput())
    if error:return error
    if not item:
        item=FacultyProfile(user_id=get_current_user().id);db.session.add(item)
    for key,value in data.items():setattr(item,key,value)
    db.session.commit();return jsonify(item.to_dict())
@faculty_bp.route('/faculty/opportunities',methods=['GET','POST'])
@roles_required('ACADEMICIAN','INDUSTRY','INSTITUTION')
def opportunities():
    user=get_current_user()
    if request.method=='GET':
        items=FacultyOpportunity.query.order_by(FacultyOpportunity.id.desc()).all()
        return jsonify([p.to_dict() for p in items if p.is_active and (not p.deadline or p.deadline>=date.today()) or p.owner_id==user.id])
    data,error=parse(FacultyInput())
    if error:return error
    if data.get('deadline') and data['deadline']<date.today():return jsonify({'error':'Deadline is in the past'}),400
    post=FacultyOpportunity(owner_id=user.id,**data)
    db.session.add(post);db.session.commit();return jsonify(post.to_dict()),201
@faculty_bp.route('/faculty/opportunities/<int:post_id>',methods=['PUT','DELETE'])
@roles_required('ACADEMICIAN','INDUSTRY','INSTITUTION')
def manage(post_id):
    post=FacultyOpportunity.query.get(post_id)
    if not post:return jsonify({'error':'Not found'}),404
    if post.owner_id!=get_current_user().id:return jsonify({'error':'Forbidden'}),403
    if request.method=='DELETE':post.is_active=False;db.session.commit();return '',204
    data,error=parse(FacultyInput())
    if error:return error
    if data.get('deadline') and data['deadline']<date.today():return jsonify({'error':'Deadline is in the past'}),400
    for key,value in data.items():setattr(post,key,value)
    db.session.commit();return jsonify(post.to_dict())
@faculty_bp.post('/faculty/opportunities/<int:post_id>/apply')
@roles_required('ACADEMICIAN')
def apply(post_id):
    post=FacultyOpportunity.query.get(post_id)
    if not post or not post.is_active or post.deadline and post.deadline<date.today():return jsonify({'error':'Opportunity unavailable'}),404
    if post.owner_id==get_current_user().id:return jsonify({'error':'Cannot apply to own opportunity'}),400
    statement=(request.get_json(silent=True) or {}).get('statement','')
    if not isinstance(statement,str) or not 5<=len(statement.strip())<=3000:return jsonify({'error':'Statement must be 5–3000 characters'}),400
    if FacultyApplication.query.filter_by(opportunity_id=post_id,applicant_id=get_current_user().id).first():return jsonify({'error':'Already applied'}),409
    item=FacultyApplication(opportunity_id=post_id,applicant_id=get_current_user().id,statement=statement.strip())
    db.session.add(item);db.session.commit();return jsonify(item.to_dict()),201
@faculty_bp.get('/faculty/applications/mine')
@roles_required('ACADEMICIAN')
def mine():
    return jsonify([{**a.to_dict(),'opportunity':a.opportunity.to_dict()} for a in FacultyApplication.query.filter_by(applicant_id=get_current_user().id).all()])
@faculty_bp.get('/faculty/opportunities/<int:post_id>/applications')
@roles_required('ACADEMICIAN','INDUSTRY','INSTITUTION')
def applicants(post_id):
    post=FacultyOpportunity.query.get(post_id)
    if not post:return jsonify({'error':'Not found'}),404
    if post.owner_id!=get_current_user().id:return jsonify({'error':'Forbidden'}),403
    return jsonify([{**a.to_dict(),'applicant':User.query.get(a.applicant_id).to_dict()} for a in post.applications])
@faculty_bp.post('/faculty/applications/<int:application_id>/shortlist')
@roles_required('ACADEMICIAN','INDUSTRY','INSTITUTION')
def shortlist(application_id):
    a=FacultyApplication.query.get(application_id)
    if not a:return jsonify({'error':'Not found'}),404
    if a.opportunity.owner_id!=get_current_user().id:return jsonify({'error':'Forbidden'}),403
    a.status='SHORTLISTED';db.session.commit();return jsonify(a.to_dict())
