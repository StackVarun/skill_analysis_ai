"""Idempotent local demo data. Set DEMO_PASSWORD (8+ characters) before running."""
import os
from app import create_app
from app.extensions import db
from app.models.user import User
from app.models.student_profile import StudentProfile
from app.models.student_skill import StudentSkill, ProficiencyLevel
from app.models.skill import Skill
from app.models.institution import InstitutionProfile
from app.models.opportunity import CompanyProfile, Opportunity, OpportunitySkill
from app.models.faculty import FacultyProfile, FacultyOpportunity

password=os.environ.get('DEMO_PASSWORD','')
if len(password)<8:raise SystemExit('Set DEMO_PASSWORD to at least 8 characters')

def user(email,first,last,role):
    item=User.query.filter_by(email=email).first()
    if not item:
        item=User(email,password,first,last,role);db.session.add(item);db.session.flush()
    return item

with create_app().app_context():
    student=user('student@demo.skillbridge','Asha','Rao','STUDENT')
    employer=user('industry@demo.skillbridge','Meera','Shah','INDUSTRY')
    faculty=user('faculty@demo.skillbridge','Arun','Kumar','ACADEMICIAN')
    admin=user('institution@demo.skillbridge','SRM','Admin','INSTITUTION')
    profile=StudentProfile.query.filter_by(user_id=student.id).first()
    if not profile:
        profile=StudentProfile(user_id=student.id,full_name='Asha Rao',institution='SRM Institute of Science and Technology',degree='B.Tech',branch='Computer Science',graduation_year=2029,bio='Backend engineering student');db.session.add(profile);db.session.flush()
    if not InstitutionProfile.query.filter_by(user_id=admin.id).first():db.session.add(InstitutionProfile(user_id=admin.id,name='SRM Institute of Science and Technology'))
    if not FacultyProfile.query.filter_by(user_id=faculty.id).first():db.session.add(FacultyProfile(user_id=faculty.id,institution='SRM Institute of Science and Technology',department='Computer Science',designation='Assistant Professor',interests='Industry research collaboration'))
    firm=CompanyProfile.query.filter_by(user_id=employer.id).first()
    if not firm:
        firm=CompanyProfile(user_id=employer.id,name='Northstar Labs',location='Chennai',description='Software engineering and data systems');db.session.add(firm);db.session.flush()
    skills=[]
    for name,level in [('Python',ProficiencyLevel.ADVANCED),('SQL',ProficiencyLevel.INTERMEDIATE),('Flask',ProficiencyLevel.INTERMEDIATE)]:
        skill=Skill.query.filter_by(name=name).first()
        if not skill:skill=Skill(name,category='Technical');db.session.add(skill);db.session.flush()
        skills.append(skill)
        if not StudentSkill.query.filter_by(student_id=profile.id,skill_id=skill.id).first():db.session.add(StudentSkill(student_id=profile.id,skill_id=skill.id,proficiency=level))
    if not Opportunity.query.filter_by(company_id=firm.id,title='Backend Engineering Intern').first():
        post=Opportunity(company_id=firm.id,title='Backend Engineering Intern',kind='INTERNSHIP',description='Build API endpoints and work on data systems.',location='Chennai',employment_type='Hybrid',eligibility='Computer Science students',duration='3 months',stipend='₹15,000/month')
        post.requirements=[OpportunitySkill(skill_id=s.id,required_proficiency=70 if s.name=='Python' else 60,weight=2 if s.name=='Python' else 1) for s in skills]
        db.session.add(post)
    if not FacultyOpportunity.query.filter_by(owner_id=employer.id,title='Industry Data Systems FDP').first():db.session.add(FacultyOpportunity(owner_id=employer.id,title='Industry Data Systems FDP',kind='FDP',description='Faculty development programme on production data systems.',organization=firm.name))
    db.session.commit()
    print('Demo accounts: student@demo.skillbridge, industry@demo.skillbridge, faculty@demo.skillbridge, institution@demo.skillbridge')
    print('Password: value supplied through DEMO_PASSWORD (existing accounts are not reset)')
