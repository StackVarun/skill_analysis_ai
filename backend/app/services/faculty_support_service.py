"""Institution-scoped reviews and student support; reuse existing skill scoring."""
from datetime import date
from sqlalchemy import func
from app.extensions import db
from app.models.faculty import FacultyProfile
from app.models.faculty_support import VerificationRequest, MentorshipTask, now
from app.models.student_profile import StudentProfile
from app.models.project import Project
from app.models.skill_evidence import SkillEvidence, VerificationStatus
from app.models.skill import Skill
from app.models.role import Role
from app.models.opportunity import OpportunityApplication, APPLICATION_STATUSES
from app.services.skill_intelligence_service import SkillIntelligenceService as Engine


class SupportError(Exception):
    def __init__(self, message, status=400):
        super().__init__(message)
        self.status = status


def institution_students(user_id):
    faculty = FacultyProfile.query.filter_by(user_id=user_id).first()
    if not faculty or not faculty.institution or not faculty.institution.strip():
        raise SupportError('Save your faculty institution before reviewing students', 403)
    return StudentProfile.query.filter(func.lower(func.trim(StudentProfile.institution)) == faculty.institution.strip().lower())


def scoped_student(user_id, student_id):
    student = institution_students(user_id).filter(StudentProfile.id == student_id).first()
    if student is None:
        raise SupportError('Student not found in your institution', 404)
    return student


def queue_review(student_id, kind, source_id, reset=False):
    """Enqueue within the caller's transaction so notifications cannot be lost."""
    column = {'PROJECT': 'project_id', 'ASSESSMENT': 'attempt_id', 'EVIDENCE': 'evidence_id'}[kind]
    review = VerificationRequest.query.filter_by(**{column: source_id}).first()
    if review is None:
        review = VerificationRequest(student_id=student_id, kind=kind, **{column: source_id})
        db.session.add(review)
    elif reset:
        review.status = 'PENDING'
        review.version += 1
        review.reviewer_id = None
        review.reviewed_at = None
        review.feedback = None
        review.student_response = None
        review.updated_at = now()
    return review


def project_changed(project):
    for evidence in SkillEvidence.query.filter_by(student_id=project.student_id, project_id=project.id).all():
        evidence.verification_status = VerificationStatus.SELF_REPORTED
        # An endorsement of linked evidence also becomes stale after editing work.
        if evidence.verification_request:
            queue_review(project.student_id, 'EVIDENCE', evidence.id, reset=True)
    if project.completion_status == 'COMPLETED':
        queue_review(project.student_id, 'PROJECT', project.id, reset=True)
    elif project.verification_request:
        project.verification_request.status = 'WITHDRAWN'
        project.verification_request.version += 1
        project.verification_request.reviewer_id = None
        project.verification_request.reviewed_at = None
        project.verification_request.feedback = None


def endorsements(student_id):
    reviews = VerificationRequest.query.filter_by(student_id=student_id, status='APPROVED').all()
    skills = set()
    for review in reviews:
        if review.project:
            skills.update(s.id for s in review.project.skills)
        elif review.attempt:
            skills.add(review.attempt.assessment.skill_id)
        elif review.evidence:
            skills.add(review.evidence.skill_id)
    return {'has_endorsements': bool(reviews), 'endorsed_items': len(reviews), 'skill_ids': sorted(skills),
            'items': [dict(id=r.id, kind=r.kind, title=r.to_dict()['title'], reviewer=r.reviewer.full_name if r.reviewer else 'Faculty',
                           reviewed_at=r.reviewed_at.isoformat() if r.reviewed_at else None) for r in reviews]}


def review_request(user_id, request_id, decision, feedback, expected_updated_at=None):
    review = db.session.get(VerificationRequest, request_id)
    if review is None:
        raise SupportError('Verification request not found', 404)
    scoped_student(user_id, review.student_id)
    if expected_updated_at is not None and expected_updated_at != review.updated_at:
        raise SupportError('This work changed after you opened it. Refresh the inbox before reviewing', 409)
    if review.status != 'PENDING':
        raise SupportError('This request has already been reviewed or withdrawn', 409)
    if decision == 'CHANGES_REQUESTED' and not feedback.strip():
        raise SupportError('Explain the changes the student needs to make')
    if review.project and review.project.completion_status != 'COMPLETED':
        raise SupportError('Only completed projects can be endorsed', 409)
    # Claim this version atomically when multiple faculty have the inbox open.
    claimed = VerificationRequest.query.filter_by(id=review.id, status='PENDING', version=review.version).update(
        dict(status=decision, version=review.version + 1, feedback=feedback.strip() or None, reviewer_id=user_id, reviewed_at=now(), updated_at=now()),
        synchronize_session=False)
    if not claimed:
        db.session.rollback()
        raise SupportError('This request changed. Refresh the inbox before reviewing', 409)
    evidence_status = VerificationStatus.VERIFIED if decision == 'APPROVED' else VerificationStatus.SELF_REPORTED
    if review.project:
        for skill in review.project.skills:
            records = SkillEvidence.query.filter_by(student_id=review.student_id, project_id=review.project.id, skill_id=skill.id).all()
            if not records and decision == 'APPROVED':
                evidence = SkillEvidence(student_id=review.student_id, skill_id=skill.id, evidence_type='PROJECT',
                                         evidence_title=review.project.title, project_id=review.project.id,
                                         source_url=review.project.project_url or review.project.github_url, evidence_strength=1.0)
                db.session.add(evidence)
                records = [evidence]
            for evidence in records:
                evidence.verification_status = evidence_status
    elif review.evidence:
        review.evidence.verification_status = evidence_status
    # Assessment scores remain machine-scored; faculty endorsement records review only.
    db.session.commit()
    return review


def faculty_summary(user_id):
    students = institution_students(user_id).all()
    ids = [s.id for s in students]
    applications = OpportunityApplication.query.filter(OpportunityApplication.student_id.in_(ids)).all()
    stage_students = {status: len({a.student_id for a in applications if a.status == status}) for status in APPLICATION_STATUSES}
    return dict(student_count=len(ids),
                selected_students=len({a.student_id for a in applications if a.status in ('SHORTLISTED', 'INTERVIEW', 'OFFER')}),
                interview_students=stage_students['INTERVIEW'], offer_students=stage_students['OFFER'],
                application_outcomes={status: sum(a.status == status for a in applications) for status in APPLICATION_STATUSES},
                pending_verifications=VerificationRequest.query.filter(VerificationRequest.student_id.in_(ids), VerificationRequest.status == 'PENDING').count(),
                active_mentorship_tasks=MentorshipTask.query.filter(MentorshipTask.faculty_id == user_id, MentorshipTask.student_id.in_(ids), MentorshipTask.status != 'COMPLETED').count(),
                supervised_projects=MentorshipTask.query.filter_by(faculty_id=user_id, kind='PROJECT_SUPERVISION').filter(MentorshipTask.student_id.in_(ids), MentorshipTask.status != 'COMPLETED', MentorshipTask.project_id.isnot(None)).with_entities(MentorshipTask.project_id).distinct().count())


def student_detail(student):
    # Merge catalog-role gaps with requirements from jobs the student applied to.
    # Numeric scores/gaps still come from the existing matching engine.
    from app.services.opportunity_service import match_candidate
    gaps = {row['skill_id']: {**row, 'source': 'Role catalog'} for row in Engine.recommendations(student.id)}
    applications = OpportunityApplication.query.filter_by(student_id=student.id).all()
    for application in applications:
        for gap in match_candidate(application.opportunity, student)['skill_gaps']:
            if gap['gap'] > gaps.get(gap['skill_id'], {}).get('gap', 0):
                gaps[gap['skill_id']] = dict(skill_id=gap['skill_id'], skill=gap['skill'],
                    current_score=gap['student_score'], required_score=gap['required_score'], gap=gap['gap'],
                    source=application.opportunity.title, priority='high' if gap['gap'] > 25 else 'medium' if gap['gap'] > 10 else 'low',
                    recommended_topics=['Review core concepts', 'Build a skill-specific project'])
    return dict(student=student.to_dict(), skills=Engine.student_scores(student.id),
                gaps=sorted(gaps.values(), key=lambda row: (-row['gap'], row['skill'])), projects=[p.to_dict() for p in student.projects],
                endorsements=endorsements(student.id),
                applications=[dict(id=a.id, title=a.opportunity.title, company=a.opportunity.company.name, status=a.status)
                              for a in OpportunityApplication.query.filter_by(student_id=student.id).all()])


def assign_task(user_id, data):
    scoped_student(user_id, data['student_id'])
    if data.get('due_date') and data['due_date'] < date.today():
        raise SupportError('Due date cannot be in the past')
    for key, model in [('skill_id', Skill), ('role_id', Role)]:
        if data.get(key) and db.session.get(model, data[key]) is None:
            raise SupportError(f'Unknown {key}')
    project = None
    if data.get('project_id'):
        project = Project.query.filter_by(id=data['project_id'], student_id=data['student_id']).first()
        if project is None:
            raise SupportError('Project must belong to this student')
    if data['kind'] == 'PROJECT_SUPERVISION' and project is None:
        raise SupportError('Choose a project to supervise')
    if data['kind'] in ('COURSEWORK', 'RESEARCH') and not data.get('skill_id'):
        raise SupportError('Choose the skill this task should develop')
    task = MentorshipTask(faculty_id=user_id, **data)
    db.session.add(task)
    db.session.commit()
    return task
