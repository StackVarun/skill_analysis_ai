"""Faculty review queues, placement summary and targeted student support."""
from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_current_user
from marshmallow import Schema, fields, validate, ValidationError
from app.extensions import db
from app.utils.decorators import roles_required
from app.models.faculty_support import VerificationRequest, MentorshipTask
from app.models.student_profile import StudentProfile
from app.services.faculty_support_service import (SupportError, institution_students, scoped_student,
    review_request, faculty_summary, student_detail, assign_task, queue_review)

support_bp = Blueprint('faculty_support', __name__)


class ReviewInput(Schema):
    expected_updated_at = fields.DateTime(allow_none=True, load_default=None)
    decision = fields.Str(required=True, validate=validate.OneOf(['APPROVED', 'CHANGES_REQUESTED']))
    feedback = fields.Str(load_default='', validate=validate.Length(max=3000))


class TaskInput(Schema):
    student_id = fields.Int(required=True)
    kind = fields.Str(required=True, validate=validate.OneOf(['COURSEWORK', 'RESEARCH', 'PROJECT_SUPERVISION']))
    title = fields.Str(required=True, validate=validate.Length(min=2, max=200))
    description = fields.Str(required=True, validate=validate.Length(min=5, max=10000))
    skill_id = fields.Int(allow_none=True, load_default=None)
    project_id = fields.Int(allow_none=True, load_default=None)
    role_id = fields.Int(allow_none=True, load_default=None)
    due_date = fields.Date(allow_none=True, load_default=None)


class StudentTaskInput(Schema):
    status = fields.Str(required=True, validate=validate.OneOf(['IN_PROGRESS', 'SUBMITTED']))
    submission = fields.Str(load_default='', validate=validate.Length(max=10000))


class FacultyTaskInput(Schema):
    status = fields.Str(required=True, validate=validate.OneOf(['IN_PROGRESS', 'COMPLETED']))
    feedback = fields.Str(load_default='', validate=validate.Length(max=3000))


def body(schema):
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        raise SupportError('Expected a JSON object')
    return schema.load(data)


@support_bp.errorhandler(SupportError)
def support_error(error):
    return jsonify({'error': str(error)}), error.status


@support_bp.errorhandler(ValidationError)
def validation_error(error):
    return jsonify({'error': 'Validation error', 'messages': error.messages}), 400


@support_bp.get('/faculty/summary')
@roles_required('ACADEMICIAN')
def summary():
    return jsonify(faculty_summary(get_current_user().id))


@support_bp.get('/faculty/students')
@roles_required('ACADEMICIAN')
def students():
    return jsonify([{**s.to_dict(), 'email': s.user.email} for s in institution_students(get_current_user().id).order_by(StudentProfile.full_name).all()])


@support_bp.get('/faculty/students/<int:student_id>')
@roles_required('ACADEMICIAN')
def detail(student_id):
    return jsonify(student_detail(scoped_student(get_current_user().id, student_id)))


@support_bp.get('/faculty/reviews')
@roles_required('ACADEMICIAN')
def reviews():
    ids = [s.id for s in institution_students(get_current_user().id).all()]
    query = VerificationRequest.query.filter(VerificationRequest.student_id.in_(ids))
    status = request.args.get('status')
    if status:
        if status not in ('PENDING', 'APPROVED', 'CHANGES_REQUESTED', 'WITHDRAWN'):
            raise SupportError('Unknown review status')
        query = query.filter_by(status=status)
    return jsonify([r.to_dict() for r in query.order_by(VerificationRequest.updated_at.desc(), VerificationRequest.id.desc()).all()])


@support_bp.post('/faculty/reviews/<int:review_id>/decision')
@roles_required('ACADEMICIAN')
def decision(review_id):
    data = body(ReviewInput())
    return jsonify(review_request(get_current_user().id, review_id, data['decision'], data['feedback'], data['expected_updated_at']).to_dict())


@support_bp.route('/faculty/tasks', methods=['GET', 'POST'])
@roles_required('ACADEMICIAN')
def tasks():
    user_id = get_current_user().id
    if request.method == 'POST':
        data = body(TaskInput())
        data['title'] = data['title'].strip()
        data['description'] = data['description'].strip()
        if len(data['title']) < 2 or len(data['description']) < 5:
            raise SupportError('Enter a task title and description')
        return jsonify(assign_task(user_id, data).to_dict()), 201
    ids = [s.id for s in institution_students(user_id).all()]
    return jsonify([t.to_dict() for t in MentorshipTask.query.filter(MentorshipTask.faculty_id == user_id,
                   MentorshipTask.student_id.in_(ids)).order_by(MentorshipTask.id.desc()).all()])


@support_bp.patch('/faculty/tasks/<int:task_id>')
@roles_required('ACADEMICIAN')
def faculty_task(task_id):
    task = MentorshipTask.query.filter_by(id=task_id, faculty_id=get_current_user().id).first()
    if task is None:
        raise SupportError('Task not found', 404)
    scoped_student(get_current_user().id, task.student_id)
    data = body(FacultyTaskInput())
    if task.status != 'SUBMITTED':
        raise SupportError('Only submitted work can be reviewed', 409)
    if data['status'] == 'IN_PROGRESS' and not data['feedback'].strip():
        raise SupportError('Explain the changes the student needs to make')
    task.status = data['status']
    task.feedback = data['feedback'].strip() or None
    db.session.commit()
    return jsonify(task.to_dict())


def current_student():
    student = StudentProfile.query.filter_by(user_id=get_current_user().id).first()
    if student is None:
        raise SupportError('Student profile required', 404)
    return student


@support_bp.get('/students/mentorship')
@roles_required('STUDENT')
def student_tasks():
    return jsonify([t.to_dict() for t in MentorshipTask.query.filter_by(student_id=current_student().id).order_by(MentorshipTask.id.desc()).all()])


@support_bp.patch('/students/mentorship/<int:task_id>')
@roles_required('STUDENT')
def student_task(task_id):
    task = MentorshipTask.query.filter_by(id=task_id, student_id=current_student().id).first()
    if task is None:
        raise SupportError('Task not found', 404)
    data = body(StudentTaskInput())
    if task.status not in ('ASSIGNED', 'IN_PROGRESS'):
        raise SupportError('This task is already submitted or completed', 409)
    if data['status'] == 'SUBMITTED' and len(data['submission'].strip()) < 5:
        raise SupportError('Describe your work or provide a submission link')
    task.status = data['status']
    task.submission = data['submission'].strip() or None
    db.session.commit()
    return jsonify(task.to_dict())


@support_bp.get('/students/reviews')
@roles_required('STUDENT')
def student_reviews():
    return jsonify([r.to_dict() for r in VerificationRequest.query.filter_by(student_id=current_student().id).order_by(VerificationRequest.updated_at.desc()).all()])


class ResubmitInput(Schema):
    response = fields.Str(required=True, validate=validate.Length(min=5, max=3000))


@support_bp.post('/students/reviews/<int:review_id>/resubmit')
@roles_required('STUDENT')
def resubmit_review(review_id):
    review = VerificationRequest.query.filter_by(id=review_id, student_id=current_student().id).first()
    if review is None:
        raise SupportError('Review not found', 404)
    if review.status != 'CHANGES_REQUESTED':
        raise SupportError('Only changes requests can be resubmitted', 409)
    data = body(ResubmitInput())
    response = data['response'].strip()
    if len(response) < 5:
        raise SupportError('Explain how you addressed the faculty feedback')
    if review.project and review.project.completion_status != 'COMPLETED':
        raise SupportError('Complete the project before resubmitting', 409)
    source = review.project_id if review.kind == 'PROJECT' else review.attempt_id if review.kind == 'ASSESSMENT' else review.evidence_id
    queue_review(review.student_id, review.kind, source, reset=True)
    review.student_response = response
    db.session.commit()
    return jsonify(review.to_dict())
