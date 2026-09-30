"""Authenticated industry and opportunity endpoints."""
from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_current_user
from marshmallow import ValidationError
from app.utils.decorators import roles_required
from app.schemas.opportunity_schema import CompanyInput, PostInput, ApplicationStatusInput
from app.services.opportunity_service import OpportunityService, OpportunityError, candidate_record

opportunity_bp = Blueprint('opportunity', __name__)


@opportunity_bp.errorhandler(OpportunityError)
def opportunity_error(exc):
    return jsonify({'error': str(exc), **exc.details}), exc.status


@opportunity_bp.errorhandler(ValidationError)
def validation_error(exc):
    return jsonify({'error': 'Validation error', 'messages': exc.messages}), 400


def payload(schema):
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        raise ValidationError({'_schema': ['Expected a JSON object.']})
    return schema.load(data)


@opportunity_bp.route('/industry/company', methods=['GET', 'PUT'])
@roles_required('INDUSTRY')
def company_profile():
    user_id = get_current_user().id
    if request.method == 'GET':
        item = OpportunityService.company(user_id)
        return jsonify(item.to_dict() if item else None)
    return jsonify(OpportunityService.save_company(user_id, payload(CompanyInput())).to_dict())


@opportunity_bp.get('/opportunities')
@roles_required('STUDENT', 'INDUSTRY')
def list_opportunities():
    return jsonify([p.to_dict() for p in OpportunityService.visible_posts(get_current_user())])


@opportunity_bp.post('/opportunities')
@roles_required('INDUSTRY')
def create_opportunity():
    post = OpportunityService.save_post(get_current_user().id, payload(PostInput()))
    return jsonify(post.to_dict()), 201


@opportunity_bp.route('/opportunities/<int:post_id>', methods=['GET', 'PUT', 'DELETE'])
@roles_required('STUDENT', 'INDUSTRY')
def opportunity_detail(post_id):
    user = get_current_user()
    if request.method == 'GET':
        return jsonify(OpportunityService.detail(post_id, user).to_dict())
    if not user.has_role('INDUSTRY'):
        raise OpportunityError('Forbidden', 403)
    OpportunityService.own_post(post_id, user.id)
    if request.method == 'DELETE':
        OpportunityService.close_post(post_id, user.id)
        return '', 204
    return jsonify(OpportunityService.save_post(user.id, payload(PostInput()), post_id).to_dict())


@opportunity_bp.post('/opportunities/<int:post_id>/apply')
@roles_required('STUDENT')
def apply(post_id):
    return jsonify(OpportunityService.apply(post_id, get_current_user().id).to_dict()), 201


@opportunity_bp.get('/applications/mine')
@roles_required('STUDENT')
def my_applications():
    return jsonify([{**a.to_dict(), 'opportunity': a.opportunity.to_dict()}
                    for a in OpportunityService.my_applications(get_current_user().id)])


@opportunity_bp.get('/opportunities/<int:post_id>/applications')
@roles_required('INDUSTRY')
def applications(post_id):
    post = OpportunityService.own_post(post_id, get_current_user().id)
    candidates = [candidate_record(a) for a in post.applications]
    candidates.sort(key=lambda item: (-item['match']['match_percentage'], item['id']))
    return jsonify(candidates)


@opportunity_bp.get('/applications/<int:application_id>')
@roles_required('INDUSTRY')
def application_detail(application_id):
    application = OpportunityService.own_application(application_id, get_current_user().id)
    return jsonify(candidate_record(application))


@opportunity_bp.post('/applications/<int:application_id>/shortlist')
@roles_required('INDUSTRY')
def shortlist(application_id):
    application = OpportunityService.own_application(application_id, get_current_user().id)
    return jsonify(candidate_record(OpportunityService.change_status(application, 'SHORTLISTED')))


@opportunity_bp.patch('/applications/<int:application_id>/status')
@roles_required('INDUSTRY')
def update_application_status(application_id):
    application = OpportunityService.own_application(application_id, get_current_user().id)
    data = payload(ApplicationStatusInput())
    return jsonify(candidate_record(OpportunityService.change_status(application, data['status'])))


@opportunity_bp.get('/industry/summary')
@roles_required('INDUSTRY')
def summary():
    return jsonify(OpportunityService.summary(get_current_user()))
