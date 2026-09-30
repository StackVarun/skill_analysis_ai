"""Repeatable local demo setup; no database changes on import."""
import argparse
import os
from app import create_app
from app.extensions import db
from app.models.user import User
from app.models.student_profile import StudentProfile
from app.models.student_skill import StudentSkill, ProficiencyLevel
from app.models.skill import Skill
from app.models.project import Project
from app.models.skill_evidence import SkillEvidence
from app.models.institution import InstitutionProfile
from app.models.opportunity import CompanyProfile, Opportunity, OpportunitySkill, OpportunityApplication
from app.models.faculty import FacultyProfile, FacultyOpportunity
from app.services.opportunity_service import is_open

INSTITUTION = 'SRM Institute of Science and Technology'
STUDENTS = [
    ('student1@test.com', 'John', 'Doe', ProficiencyLevel.EXPERT, 3),
    ('student2@test.com', 'Jane', 'Smith', ProficiencyLevel.ADVANCED, 2),
    ('student3@test.com', 'Daniel', 'Thomas', ProficiencyLevel.INTERMEDIATE, 2),
    ('student4@test.com', 'Sarah', 'James', ProficiencyLevel.INTERMEDIATE, 1),
    ('student5@test.com', 'David', 'Joseph', ProficiencyLevel.BEGINNER, 0),
]


def ensure_user(email, first, last, role, password, reset_passwords):
    item = User.query.filter_by(email=email).first()
    if item is None:
        item = User(email, password, first, last, role)
        db.session.add(item)
        db.session.flush()
    elif not item.has_role(role):
        raise ValueError(f'{email} already exists with a different role')
    elif reset_passwords:
        item.set_password(password)
        item.is_active = True
    return item


def ensure_profile(student):
    profile = StudentProfile.query.filter_by(user_id=student.id).first()
    if profile is None:
        profile = StudentProfile(user_id=student.id)
        db.session.add(profile)
        db.session.flush()
    for key, value in dict(full_name=student.full_name, institution=INSTITUTION,
                           degree='B.Tech', branch='Computer Science', graduation_year=2029,
                           bio='Synthetic local demo profile for candidate comparison.').items():
        if not getattr(profile, key):
            setattr(profile, key, value)
    return profile


def seed_demo(password, reset_passwords=False, opportunity_id=None):
    """Use inside an app context after migrations; preserve existing portfolio data."""
    if len(password) < 8:
        raise ValueError('Set DEMO_PASSWORD to at least 8 characters')
    if opportunity_id is not None:
        post = db.session.get(Opportunity, opportunity_id)
        if post is None or not is_open(post) or not post.requirements:
            raise ValueError('Choose an existing open posting with required skills')
    else:
        jobs = [p for p in Opportunity.query.filter_by(kind='JOB').order_by(Opportunity.id).all() if is_open(p)]
        if len(jobs) > 1:
            raise ValueError('Several open jobs exist. Specify --opportunity-id to choose one')
        post = jobs[0] if jobs else None
        if post is not None and not post.requirements:
            raise ValueError('Add required skills to the existing job before seeding applicants')
    employer = ensure_user('industry@demo.skillbridge', 'Meera', 'Shah', 'INDUSTRY', password, reset_passwords)
    faculty = ensure_user('faculty@demo.skillbridge', 'Arun', 'Kumar', 'ACADEMICIAN', password, reset_passwords)
    admin = ensure_user('institution@demo.skillbridge', 'SRM', 'Admin', 'INSTITUTION', password, reset_passwords)
    student = ensure_user('student@demo.skillbridge', 'Asha', 'Rao', 'STUDENT', password, reset_passwords)
    ensure_profile(student)
    if not InstitutionProfile.query.filter_by(user_id=admin.id).first():
        db.session.add(InstitutionProfile(user_id=admin.id, name=INSTITUTION))
    if not FacultyProfile.query.filter_by(user_id=faculty.id).first():
        db.session.add(FacultyProfile(user_id=faculty.id, institution=INSTITUTION, department='Computer Science', designation='Assistant Professor', interests='Industry research collaboration'))
    firm = CompanyProfile.query.filter_by(user_id=employer.id).first()
    if firm is None:
        firm = CompanyProfile(user_id=employer.id, name='Northstar Labs', location='Chennai', description='Software engineering and data systems')
        db.session.add(firm)
        db.session.flush()
    if post is None:
        skills = []
        for name in ('Python', 'SQL', 'Flask'):
            skill = Skill.query.filter(db.func.lower(Skill.name) == name.lower()).first()
            if skill is None:
                skill = Skill(name, category='Technical')
                db.session.add(skill)
                db.session.flush()
            skills.append(skill)
        post = Opportunity(company_id=firm.id, title='Backend Engineer', kind='JOB', description='Build API endpoints and work on data systems.', location='Chennai', employment_type='Hybrid', eligibility='Computer Science students')
        post.requirements = [OpportunitySkill(skill_id=s.id, required_proficiency=70 if s.name.lower() == 'python' else 60, weight=2 if s.name.lower() == 'python' else 1) for s in skills]
        db.session.add(post)
        db.session.flush()
    profiles = []
    for email, first, last, level, project_count in STUDENTS:
        account = ensure_user(email, first, last, 'STUDENT', password, reset_passwords)
        profile = ensure_profile(account)
        profiles.append(profile)
        for requirement in post.requirements:
            if not StudentSkill.query.filter_by(student_id=profile.id, skill_id=requirement.skill_id).first():
                db.session.add(StudentSkill(student_id=profile.id, skill_id=requirement.skill_id, proficiency=level))
        # Synthetic evidence stays self reported; never claim faculty verification.
        for number in range(1, project_count + 1):
            title = f'Demo portfolio {post.id}: project {number}'
            project = Project.query.filter_by(student_id=profile.id, title=title).first()
            if project is None:
                project = Project(student_id=profile.id, title=title, description='Synthetic demo project for applicant comparison; not a real credential.')
                project.skills = [r.skill for r in post.requirements]
                db.session.add(project)
                db.session.flush()
                from app.services.faculty_support_service import project_changed
                project_changed(project)
            for requirement in post.requirements:
                if not SkillEvidence.query.filter_by(student_id=profile.id, skill_id=requirement.skill_id, project_id=project.id).first():
                    db.session.add(SkillEvidence(student_id=profile.id, skill_id=requirement.skill_id, evidence_type='PROJECT', evidence_title=title, description='Synthetic local demo evidence, self reported.', project_id=project.id, evidence_strength=1.0))
        if not OpportunityApplication.query.filter_by(opportunity_id=post.id, student_id=profile.id).first():
            db.session.add(OpportunityApplication(opportunity_id=post.id, student_id=profile.id))
    if not FacultyOpportunity.query.filter_by(owner_id=employer.id, title='Industry Data Systems FDP').first():
        db.session.add(FacultyOpportunity(owner_id=employer.id, title='Industry Data Systems FDP', kind='FDP', description='Faculty development programme on production data systems.', organization=firm.name))
    db.session.commit()
    return post, profiles


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--reset-passwords', action='store_true', help='Reset only the named demo/test accounts to DEMO_PASSWORD and reactivate them')
    parser.add_argument('--opportunity-id', type=int, help='Existing posting that the five students should apply to')
    args = parser.parse_args()
    with create_app().app_context():
        try:
            post, profiles = seed_demo(os.environ.get('DEMO_PASSWORD', ''), args.reset_passwords, args.opportunity_id)
        except ValueError as exc:
            db.session.rollback()
            raise SystemExit(str(exc))
        owner = db.session.get(User, post.company.user_id)
        print(f'Five student applications ready for posting #{post.id}: {post.title}')
        print(f'View applicants using the owning industry account: {owner.email}')
        print('Student accounts: ' + ', '.join(email for email, *_ in STUDENTS))
        print('Demo logins: student@demo.skillbridge, industry@demo.skillbridge, faculty@demo.skillbridge, institution@demo.skillbridge')
        print('Password: DEMO_PASSWORD for new accounts' + (' and reset demo/test accounts' if args.reset_passwords else '; existing passwords unchanged'))


if __name__ == '__main__':
    main()
