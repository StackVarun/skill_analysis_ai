from flask_jwt_extended import create_access_token
from app.extensions import db
from app.models.user import User
from app.models.student_profile import StudentProfile
from app.models.skill import Skill
from app.models.student_skill import StudentSkill, ProficiencyLevel
from app.models.institution import InstitutionProfile

def token(user):return {'Authorization':'Bearer '+create_access_token(identity=user)}

def test_industry_flow(client,app):
    with app.app_context():
        student=User('stu@example.com','password123','A','Student')
        employer=User('emp@example.com','password123','A','Employer',role='INDUSTRY')
        stranger=User('stranger@example.com','password123','B','Employer',role='INDUSTRY')
        db.session.add_all([student,employer,stranger]);db.session.flush()
        profile=StudentProfile(user_id=student.id,full_name='A Student',institution='Test University')
        skill=Skill('Python');db.session.add_all([profile,skill]);db.session.flush()
        db.session.add(StudentSkill(student_id=profile.id,skill_id=skill.id,proficiency=ProficiencyLevel.ADVANCED));db.session.commit()
        st,em,ot=token(student),token(employer),token(stranger);sid=skill.id
    assert client.post('/api/opportunities',headers=st,json={}).status_code==403
    assert client.put('/api/industry/company',headers=em,json={'name':'Acme Labs'}).status_code==200
    body={'title':'Python Internship','description':'Build services with Python','kind':'INTERNSHIP','required_skills':[{'skill_id':sid,'required_proficiency':70,'weight':1}]}
    response=client.post('/api/opportunities',headers=em,json=body)
    assert response.status_code==201,response.json
    pid=response.json['id']
    assert client.get(f'/api/opportunities/{pid}/applications',headers=ot).status_code==403
    assert client.post(f'/api/opportunities/{pid}/apply',headers=st).status_code==201
    assert client.post(f'/api/opportunities/{pid}/apply',headers=st).status_code==409
    candidates=client.get(f'/api/opportunities/{pid}/applications',headers=em)
    assert candidates.status_code==200,candidates.json
    c=candidates.json[0]
    assert c['match']['match_percentage']>0 and c['student']['full_name']=='A Student'
    assert client.post(f"/api/applications/{c['id']}/shortlist",headers=ot).status_code==403
    assert client.post(f"/api/applications/{c['id']}/shortlist",headers=em).json['status']=='SHORTLISTED'
    assert client.get('/api/applications/mine',headers=st).json[0]['status']=='SHORTLISTED'
    assert client.get('/api/passport/me',headers=st).json['student']['full_name']=='A Student'

def test_faculty_analytics_scope(client,app):
    with app.app_context():
        a=User('fac@example.com','password123','A','Faculty',role='ACADEMICIAN')
        b=User('fac2@example.com','password123','B','Faculty',role='ACADEMICIAN')
        admin=User('admin@example.com','password123','C','Admin',role='INSTITUTION')
        db.session.add_all([a,b,admin]);db.session.flush()
        db.session.add(InstitutionProfile(user_id=admin.id,name='Test University'));db.session.commit()
        fa,fb,ia=token(a),token(b),token(admin)
    assert client.post('/api/auth/register',json={'email':'fake@example.com','password':'password123','first_name':'X','last_name':'Y','role':'INSTITUTION'}).status_code==403
    assert client.put('/api/faculty/profile',headers=fa,json={'institution':'Test University'}).status_code==200
    r=client.post('/api/faculty/opportunities',headers=fa,json={'title':'Research Partner','kind':'RESEARCH_COLLABORATION','description':'Joint lab study'})
    assert r.status_code==201,r.json
    pid=r.json['id']
    assert client.post(f'/api/faculty/opportunities/{pid}/apply',headers=fb,json={'statement':'I can collaborate'}).status_code==201
    assert client.get(f'/api/faculty/opportunities/{pid}/applications',headers=fb).status_code==403
    assert len(client.get(f'/api/faculty/opportunities/{pid}/applications',headers=fa).json)==1
    assert client.get('/api/institution/analytics',headers=fa).status_code==403
    result=client.get('/api/institution/analytics',headers=ia)
    assert result.status_code==200,result.json
    assert result.json['institution']=='Test University'
