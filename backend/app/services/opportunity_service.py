"""Opportunity workflows; all candidate scores come from Phase 3."""
from datetime import date
from sqlalchemy.exc import IntegrityError
from app.extensions import db
from app.models.role import Role, RoleSkillRequirement
from app.models.skill import Skill
from app.models.student_profile import StudentProfile
from app.models.skill_evidence import SkillEvidence
from app.models.opportunity import (CompanyProfile, Opportunity, OpportunitySkill,
                                    OpportunityApplication, APPLICATION_TRANSITIONS)
from app.services.skill_intelligence_service import SkillIntelligenceService


class OpportunityError(Exception):
    def __init__(self, message, status=400, **details):
        super().__init__(message)
        self.status = status
        self.details = details


def is_open(post):
    # The deadline is inclusive, matching the existing date-only posting API.
    return post.is_active and (not post.deadline or post.deadline >= date.today())


def match_candidate(post, student):
    # Transient adapter: never persist a duplicate role or calculate new scores.
    role = Role(name=post.title)
    role.requirements = [RoleSkillRequirement(
        skill_id=r.skill_id, required_proficiency=r.required_proficiency,
        weight=r.weight, skill=r.skill) for r in post.requirements]
    result = SkillIntelligenceService.analyze_role(student.id, role)
    ids = {r.skill_id for r in post.requirements}
    result['matching_skills'] = [row for row in result['required_skills'] if row['gap'] == 0]
    result['evidence'] = [
        {**e.to_dict(), 'type': e.evidence_type.value, 'status': e.verification_status.value}
        for e in SkillEvidence.query.filter_by(student_id=student.id).order_by(SkillEvidence.id).all()
        if e.skill_id in ids
    ]
    result['relevant_projects'] = [p.to_dict() for p in student.projects if any(s.id in ids for s in p.skills)]
    result['relevant_experience'] = [e.to_dict() for e in student.experiences if any(s.id in ids for s in e.skills)]
    result['relevant_internships'] = [i.to_dict() for i in student.internships if any(s.id in ids for s in i.skills)]
    return result


def candidate_record(application):
    student = application.student
    return {**application.to_dict(), 'student': student.to_dict(),
            'projects': [p.to_dict() for p in student.projects],
            'certifications': [c.to_dict() for c in student.certifications],
            'experience': [e.to_dict() for e in student.experiences],
            'internships': [i.to_dict() for i in student.internships],
            'match': match_candidate(application.opportunity, student)}


class OpportunityService:
    @staticmethod
    def company(user_id):
        return CompanyProfile.query.filter_by(user_id=user_id).first()

    @staticmethod
    def save_company(user_id, data):
        firm = OpportunityService.company(user_id)
        if firm is None:
            firm = CompanyProfile(user_id=user_id)
            db.session.add(firm)
        for key, value in data.items():
            setattr(firm, key, value)
        db.session.commit()
        return firm

    @staticmethod
    def own_post(post_id, user_id):
        post = db.session.get(Opportunity, post_id)
        if post is None:
            raise OpportunityError('Not found', 404)
        if post.company.user_id != user_id:
            raise OpportunityError('Forbidden', 403)
        return post

    @staticmethod
    def visible_posts(user):
        query = Opportunity.query
        if user.has_role('INDUSTRY'):
            query = query.join(CompanyProfile).filter(CompanyProfile.user_id == user.id)
        else:
            query = query.filter(Opportunity.is_active.is_(True),
                                 db.or_(Opportunity.deadline.is_(None), Opportunity.deadline >= date.today()))
        return query.order_by(Opportunity.created_at.desc(), Opportunity.id.desc()).all()

    @staticmethod
    def detail(post_id, user):
        if user.has_role('INDUSTRY'):
            return OpportunityService.own_post(post_id, user.id)
        post = db.session.get(Opportunity, post_id)
        if post is None or not is_open(post):
            raise OpportunityError('Not found', 404)
        return post

    @staticmethod
    def save_post(user_id, data, post_id=None):
        post = OpportunityService.own_post(post_id, user_id) if post_id is not None else None
        firm = OpportunityService.company(user_id)
        if firm is None:
            raise OpportunityError('Create a company profile first')
        data = dict(data)
        required = data.pop('required_skills')
        ids = {r['skill_id'] for r in required}
        if len(ids) != len(required):
            raise OpportunityError('Duplicate required skill')
        if Skill.query.filter(Skill.id.in_(ids)).count() != len(ids):
            raise OpportunityError('Unknown skill')
        if data.get('deadline') and data['deadline'] < date.today():
            raise OpportunityError('Deadline is in the past')
        if post is None:
            post = Opportunity(company_id=firm.id)
            db.session.add(post)
        for key, value in data.items():
            setattr(post, key, value)
        # Update retained requirements in place to avoid composite-key collisions.
        existing = {r.skill_id: r for r in post.requirements}
        requirements = []
        for item in required:
            requirement = existing.get(item['skill_id'])
            if requirement is None:
                requirement = OpportunitySkill(skill_id=item['skill_id'])
            requirement.weight = item['weight']
            requirement.required_proficiency = item['required_proficiency']
            requirements.append(requirement)
        post.requirements = requirements
        db.session.commit()
        return post

    @staticmethod
    def close_post(post_id, user_id):
        post = OpportunityService.own_post(post_id, user_id)
        post.is_active = False
        db.session.commit()

    @staticmethod
    def apply(post_id, user_id):
        post = db.session.get(Opportunity, post_id)
        if post is None or not is_open(post):
            raise OpportunityError('Opportunity unavailable', 404)
        student = StudentProfile.query.filter_by(user_id=user_id).first()
        if student is None:
            raise OpportunityError('Student profile required')
        if OpportunityApplication.query.filter_by(opportunity_id=post_id, student_id=student.id).first():
            raise OpportunityError('Already applied', 409)
        application = OpportunityApplication(opportunity_id=post_id, student_id=student.id)
        db.session.add(application)
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            # The unique constraint also handles two simultaneous submissions.
            if OpportunityApplication.query.filter_by(opportunity_id=post_id, student_id=student.id).first():
                raise OpportunityError('Already applied', 409)
            raise
        return application

    @staticmethod
    def my_applications(user_id):
        return (OpportunityApplication.query.join(StudentProfile)
                .filter(StudentProfile.user_id == user_id)
                .order_by(OpportunityApplication.created_at.desc(), OpportunityApplication.id.desc()).all())

    @staticmethod
    def own_application(application_id, user_id):
        application = db.session.get(OpportunityApplication, application_id)
        if application is None:
            raise OpportunityError('Not found', 404)
        OpportunityService.own_post(application.opportunity_id, user_id)
        return application

    @staticmethod
    def change_status(application, next_status):
        allowed = APPLICATION_TRANSITIONS.get(application.status, ())
        if next_status != application.status:
            if next_status not in allowed:
                raise OpportunityError('Invalid application status change', 409,
                                       current_status=application.status, allowed_statuses=list(allowed))
            application.status = next_status
            db.session.commit()
        return application

    @staticmethod
    def summary(user):
        posts = OpportunityService.visible_posts(user)
        applications = [application for post in posts for application in post.applications]
        return {'jobs': sum(p.kind == 'JOB' and is_open(p) for p in posts),
                'internships': sum(p.kind == 'INTERNSHIP' and is_open(p) for p in posts),
                'applications': len(applications),
                'shortlisted': sum(a.status == 'SHORTLISTED' for a in applications),
                'offers': sum(a.status == 'OFFER' for a in applications),
                'rejected': sum(a.status == 'REJECTED' for a in applications)}
