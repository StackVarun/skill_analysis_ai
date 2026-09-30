"""Faculty reviews, tamper resistance, mentorship and scoped outcomes."""
import pytest
from flask_jwt_extended import create_access_token
from app.extensions import db
from app.models.user import User
from app.models.student_profile import StudentProfile
from app.models.student_skill import StudentSkill, ProficiencyLevel
from app.models.faculty import FacultyProfile
from app.models.skill import Skill
from app.models.project import Project
from app.models.faculty_support import VerificationRequest, MentorshipTask
from app.models.skill_evidence import SkillEvidence, VerificationStatus
from app.models.assessment import AssessmentAttempt
from app.models.opportunity import CompanyProfile, Opportunity, OpportunitySkill, OpportunityApplication
from app.services.skill_intelligence_service import SkillIntelligenceService as Engine


@pytest.fixture
def people(app):
    with app.app_context():
        users = {}
        headers = {}
        for key, role in [('student', 'STUDENT'), ('other_student', 'STUDENT'), ('faculty', 'ACADEMICIAN'), ('colleague', 'ACADEMICIAN'), ('outside', 'ACADEMICIAN'), ('industry', 'INDUSTRY')]:
            user = User(f'{key}@test.com', 'password123', key, 'User', role)
            db.session.add(user); db.session.flush()
            users[key] = user
            headers[key] = {'Authorization': f'Bearer {create_access_token(identity=user)}'}
        student = StudentProfile(user_id=users['student'].id, full_name='Student One', institution='Test University')
        other = StudentProfile(user_id=users['other_student'].id, full_name='Other Student', institution='Another University')
        db.session.add_all([student, other]); db.session.flush()
        for key in ('faculty', 'colleague', 'outside'):
            db.session.add(FacultyProfile(user_id=users[key].id, institution='Another University' if key == 'outside' else ' test university '))
        skill = Skill('Python', category='Technical')
        db.session.add(skill); db.session.flush()
        db.session.add(StudentSkill(student_id=student.id, skill_id=skill.id, proficiency=ProficiencyLevel.ADVANCED))
        firm = CompanyProfile(user_id=users['industry'].id, name='Test Company')
        db.session.add(firm); db.session.flush()
        post = Opportunity(company_id=firm.id, title='Backend Job', description='Python work', kind='JOB')
        post.requirements = [OpportunitySkill(skill_id=skill.id, required_proficiency=80, weight=2)]
        db.session.add(post); db.session.commit()
        return dict(headers=headers, student_id=student.id, other_student_id=other.id, skill_id=skill.id, post_id=post.id, faculty_id=users['faculty'].id)


def create_project(client, people, **extra):
    response = client.post('/api/students/projects', headers=people['headers']['student'], json={
        'title': 'API project', 'description': 'Build endpoints', 'skill_ids': [people['skill_id']],
        'start_date': '2026-09-01', 'github_url': 'https://github.com/example/project', **extra})
    assert response.status_code == 201, response.get_json()
    return response.get_json()


def pending(client, people):
    return client.get('/api/faculty/reviews?status=PENDING', headers=people['headers']['faculty']).get_json()


def test_project_review_badge_and_edit_invalidation(app, client, people):
    project = create_project(client, people)
    assert project['verification_status'] == 'PENDING'
    inbox = pending(client, people)
    assert len(inbox) == 1 and inbox[0]['project']['title'] == project['title']
    review_id = inbox[0]['id']
    faculty = people['headers']['faculty']
    student = people['headers']['student']
    assert client.post(f'/api/faculty/reviews/{review_id}/decision', headers=student, json={'decision':'APPROVED'}).status_code == 403
    assert client.post(f'/api/faculty/reviews/{review_id}/decision', headers=people['headers']['outside'], json={'decision':'APPROVED'}).status_code == 404
    approved = client.post(f'/api/faculty/reviews/{review_id}/decision', headers=faculty, json={'decision':'APPROVED', 'feedback':'Reviewed code and skill evidence'})
    assert approved.status_code == 200
    assert approved.get_json()['project']['verification_status'] == 'APPROVED'
    passport = client.get('/api/passport/me', headers=student).get_json()
    assert passport['endorsements']['has_endorsements'] is True
    assert passport['skills'][0]['faculty_endorsed'] is True
    assert len(passport['endorsements']['items']) == 1
    with app.app_context():
        evidence = SkillEvidence.query.filter_by(project_id=project['id']).one()
        assert evidence.verification_status == VerificationStatus.VERIFIED
        assert Engine.student_scores(people['student_id'])[0]['evidence_score'] == 30
    assert client.post(f'/api/faculty/reviews/{review_id}/decision', headers=faculty, json={'decision':'APPROVED'}).status_code == 409
    # An unchanged save preserves the endorsement; actual edits require new review.
    same = client.put(f"/api/students/projects/{project['id']}", headers=student, json={'title': project['title']})
    assert same.get_json()['verification_status'] == 'APPROVED'
    changed = client.put(f"/api/students/projects/{project['id']}", headers=student, json={'title':'Edited API project'})
    assert changed.status_code == 200
    assert changed.get_json()['start_date'] == '2026-09-01'
    assert changed.get_json()['verification_status'] == 'PENDING'
    assert client.get('/api/passport/me', headers=student).get_json()['endorsements']['has_endorsements'] is False
    with app.app_context():
        assert SkillEvidence.query.filter_by(project_id=project['id']).one().verification_status == VerificationStatus.SELF_REPORTED
    assert len(pending(client, people)) == 1


def test_completion_changes_feedback_and_project_delete(app, client, people):
    project = create_project(client, people, completion_status='IN_PROGRESS')
    assert project['verification_status'] == 'NOT_REQUESTED'
    assert not pending(client, people)
    path = f"/api/students/projects/{project['id']}"
    student = people['headers']['student']; faculty = people['headers']['faculty']
    assert client.put(path, headers=student, json={'completion_status':'COMPLETED'}).get_json()['verification_status'] == 'PENDING'
    review_id = pending(client, people)[0]['id']
    review_path = f'/api/faculty/reviews/{review_id}/decision'
    assert client.post(review_path, headers=faculty, json={'decision':'CHANGES_REQUESTED'}).status_code == 400
    assert client.post(review_path, headers=faculty, json={'decision':'CHANGES_REQUESTED','feedback':'Add tests and documentation'}).status_code == 200
    mine = client.get('/api/students/reviews', headers=student).get_json()
    assert mine[0]['feedback'] == 'Add tests and documentation'
    assert client.put(path, headers=student, json={'description':'Added tests and documentation'}).get_json()['verification_status'] == 'PENDING'
    assert client.put(path, headers=student, json={'completion_status':'IN_PROGRESS'}).get_json()['verification_status'] == 'WITHDRAWN'
    assert client.post(review_path, headers=faculty, json={'decision':'APPROVED'}).status_code == 409
    assert client.delete(path, headers=student).status_code == 200
    with app.app_context():
        assert not VerificationRequest.query.filter_by(project_id=project['id']).first()


def test_assessment_completion_queues_review_without_changing_score(app, client, people):
    with app.app_context():
        assessment = Engine.create_assessment('Python basics', people['skill_id'], questions=[{'skill_id':people['skill_id'], 'prompt':'List syntax?', 'options':['[]','{}'], 'correct_answer':'[]'}])
        assessment_id = assessment.id; question_id = assessment.questions[0].id
    result = client.post(f'/api/assessments/{assessment_id}/submit', headers=people['headers']['student'], json={'answers':[{'question_id':question_id,'answer':'[]'}]})
    assert result.status_code == 201 and result.get_json()['score'] == 100
    review = pending(client, people)[0]
    assert review['kind'] == 'ASSESSMENT' and review['assessment']['score'] == 100
    assert client.post(f"/api/faculty/reviews/{review['id']}/decision", headers=people['headers']['faculty'], json={'decision':'APPROVED'}).status_code == 200
    with app.app_context():
        assert db.session.get(AssessmentAttempt, result.get_json()['id']).score == 100
    passport = client.get('/api/passport/me', headers=people['headers']['student']).get_json()
    assert passport['skills'][0]['faculty_endorsed'] is True


def test_evidence_cannot_be_self_verified_and_edits_reset_review(client, people):
    student = people['headers']['student']; faculty = people['headers']['faculty']
    payload = {'skill_id': people['skill_id'], 'evidence_type':'COURSEWORK', 'evidence_title':'Python coursework'}
    assert client.post('/api/students/skill-evidence', headers=student, json={**payload,'verification_status':'VERIFIED'}).status_code == 403
    response = client.post('/api/students/skill-evidence', headers=student, json=payload)
    assert response.status_code == 201
    evidence_id = response.get_json()['id']
    path = f'/api/students/skill-evidence/{evidence_id}'
    assert client.put(path, headers=student, json={'verification_status':'VERIFIED'}).status_code == 403
    review = pending(client, people)[0]
    assert client.post(f"/api/faculty/reviews/{review['id']}/decision", headers=faculty, json={'decision':'APPROVED'}).status_code == 200
    assert client.get(path, headers=student).get_json()['verification_status'] == 'VERIFIED'
    updated = client.put(path, headers=student, json={'evidence_title':'Updated coursework'})
    assert updated.get_json()['verification_status'] == 'SELF_REPORTED'
    assert len(pending(client, people)) == 1
    assert not client.get('/api/passport/me', headers=student).get_json()['endorsements']['has_endorsements']


def test_mentorship_submission_supervision_and_access(app, client, people):
    faculty = people['headers']['faculty']; student = people['headers']['student']
    project = create_project(client, people, completion_status='IN_PROGRESS')
    payload = {'student_id':people['student_id'], 'kind':'COURSEWORK', 'skill_id':people['skill_id'], 'title':'Practice SQL joins', 'description':'Complete a focused exercise and submit your code'}
    assert client.post('/api/faculty/tasks', headers=faculty, json={**payload,'student_id':people['other_student_id']}).status_code == 404
    assert client.post('/api/faculty/tasks', headers=faculty, json={**payload,'title':'  '}).status_code == 400
    assert client.post('/api/faculty/tasks', headers=faculty, json={**payload,'due_date':'2000-01-01'}).status_code == 400
    assert client.post('/api/faculty/tasks', headers=faculty, json={**payload,'kind':'PROJECT_SUPERVISION'}).status_code == 400
    supervised = client.post('/api/faculty/tasks', headers=faculty, json={**payload,'kind':'PROJECT_SUPERVISION','project_id':project['id']})
    assert supervised.status_code == 201
    task = client.post('/api/faculty/tasks', headers=faculty, json=payload).get_json()
    path = f"/api/students/mentorship/{task['id']}"
    assert client.patch(path, headers=people['headers']['other_student'], json={'status':'IN_PROGRESS'}).status_code == 404
    assert client.patch(path, headers=student, json={'status':'COMPLETED'}).status_code == 400
    assert client.patch(f"/api/faculty/tasks/{task['id']}", headers=faculty, json={'status':'COMPLETED'}).status_code == 409
    assert client.patch(path, headers=student, json={'status':'IN_PROGRESS'}).status_code == 200
    assert client.patch(path, headers=student, json={'status':'SUBMITTED','submission':'x'}).status_code == 400
    assert client.patch(path, headers=student, json={'status':'SUBMITTED','submission':'Completed exercises: https://example.com/my-work'}).status_code == 200
    review_path = f"/api/faculty/tasks/{task['id']}"
    assert client.patch(review_path, headers=people['headers']['colleague'], json={'status':'COMPLETED'}).status_code == 404
    assert client.patch(review_path, headers=faculty, json={'status':'IN_PROGRESS','feedback':'Add edge cases'}).status_code == 200
    assert client.patch(path, headers=student, json={'status':'SUBMITTED','submission':'Added edge cases and submitted revised code'}).status_code == 200
    assert client.patch(review_path, headers=faculty, json={'status':'COMPLETED','feedback':'Well done'}).status_code == 200
    assert client.patch(path, headers=student, json={'status':'IN_PROGRESS'}).status_code == 409
    mine = client.get('/api/students/mentorship', headers=student).get_json()
    assert len(mine) == 2
    assert any(t['feedback'] == 'Well done' for t in mine)
    assert client.get('/api/faculty/summary', headers=faculty).get_json()['supervised_projects'] == 1
    # Removing a project removes its endorsement request, but preserves supervision history.
    client.delete(f"/api/students/projects/{project['id']}", headers=student)
    with app.app_context():
        assert db.session.get(MentorshipTask, supervised.get_json()['id']).project_id is None


def test_summary_scope_and_current_outcomes(app, client, people):
    with app.app_context():
        db.session.add_all([OpportunityApplication(opportunity_id=people['post_id'], student_id=people['student_id'],status='INTERVIEW'), OpportunityApplication(opportunity_id=people['post_id'], student_id=people['other_student_id'],status='OFFER')]);db.session.commit()
    faculty = people['headers']['faculty']
    summary = client.get('/api/faculty/summary', headers=faculty).get_json()
    assert summary['student_count'] == 1
    assert summary['selected_students'] == 1 and summary['interview_students'] == 1 and summary['offer_students'] == 0
    assert summary['application_outcomes']['INTERVIEW'] == 1
    assert summary['application_outcomes']['OFFER'] == 0
    students = client.get('/api/faculty/students', headers=faculty).get_json()
    assert [s['id'] for s in students] == [people['student_id']]
    detail = client.get(f"/api/faculty/students/{people['student_id']}", headers=faculty).get_json()
    assert detail['gaps'][0]['source'] == 'Backend Job'
    assert detail['gaps'][0]['required_score'] == 80
    assert client.get(f"/api/faculty/students/{people['other_student_id']}",headers=faculty).status_code == 404
    for key in ('student','industry'):
        assert client.get('/api/faculty/summary',headers=people['headers'][key]).status_code == 403
    with app.app_context():
        FacultyProfile.query.filter_by(user_id=people['faculty_id']).delete();db.session.commit()
    assert client.get('/api/faculty/students',headers=faculty).status_code == 403


def test_stale_review_and_invalid_project_skills(client, people):
    project = create_project(client, people)
    review = pending(client, people)[0]
    student = people['headers']['student']
    path = f"/api/students/projects/{project['id']}"
    invalid = client.put(path, headers=student, json={'title':'Bad update','skill_ids':[999999]})
    assert invalid.status_code == 400
    assert client.get(path, headers=student).get_json()['title'] == project['title']
    assert client.put(path, headers=student, json={'title':'Changed work'}).status_code == 200
    stale = client.post(f"/api/faculty/reviews/{review['id']}/decision", headers=people['headers']['faculty'],
                        json={'decision':'APPROVED', 'expected_updated_at':review['updated_at']})
    assert stale.status_code == 409
    current = pending(client, people)[0]
    assert client.post(f"/api/faculty/reviews/{review['id']}/decision", headers=people['headers']['faculty'],
                        json={'decision':'APPROVED', 'expected_updated_at':current['updated_at']}).status_code == 200


def test_student_can_respond_to_assessment_changes_without_rescoring(app, client, people):
    with app.app_context():
        assessment = Engine.create_assessment('Assessment review', people['skill_id'], questions=[{'skill_id':people['skill_id'],'prompt':'Pick the list','options':['[]','{}'],'correct_answer':'[]'}])
        assessment_id=assessment.id; question_id=assessment.questions[0].id
    student=people['headers']['student']; faculty=people['headers']['faculty']
    attempt=client.post(f'/api/assessments/{assessment_id}/submit',headers=student,json={'answers':[{'question_id':question_id,'answer':'{}'}]}).get_json()
    review=pending(client,people)[0]
    assert client.post(f"/api/faculty/reviews/{review['id']}/decision",headers=faculty,json={'decision':'CHANGES_REQUESTED','feedback':'Explain the concept you misunderstood'}).status_code==200
    path=f"/api/students/reviews/{review['id']}/resubmit"
    assert client.post(path,headers=people['headers']['other_student'],json={'response':'I practiced the concepts'}).status_code==404
    assert client.post(path,headers=student,json={'response':'   '}).status_code==400
    result=client.post(path,headers=student,json={'response':'I practiced Python lists and can explain the corrected answer'})
    assert result.status_code==200 and result.get_json()['status']=='PENDING'
    assert result.get_json()['student_response'].startswith('I practiced')
    assert result.get_json()['assessment']['score']==0
    assert client.post(path,headers=student,json={'response':'Repeated response'}).status_code==409
    assert client.post(f"/api/faculty/reviews/{review['id']}/decision",headers=faculty,json={'decision':'APPROVED','expected_updated_at':result.get_json()['updated_at']}).status_code==200
    with app.app_context():
        assert db.session.get(AssessmentAttempt,attempt['id']).score==0
