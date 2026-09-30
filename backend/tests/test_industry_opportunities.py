"""Phase 5A workflow, access isolation, and deterministic matching regressions."""
from copy import deepcopy
from datetime import date, timedelta
from unittest.mock import patch
import pytest
from flask_jwt_extended import create_access_token
from sqlalchemy.exc import IntegrityError
from app.extensions import db
from app.models.user import User
from app.models.student_profile import StudentProfile
from app.models.skill import Skill
from app.models.student_skill import StudentSkill, ProficiencyLevel
from app.models.project import Project
from app.models.skill_evidence import SkillEvidence
from app.models.role import Role, RoleSkillRequirement
from app.models.opportunity import Opportunity, OpportunityApplication
from app.services.skill_intelligence_service import SkillIntelligenceService


@pytest.fixture
def scenario(client, app):
    users = {}
    for key, role in [('student', 'STUDENT'), ('other_student', 'STUDENT'),
                      ('industry', 'INDUSTRY'), ('other_industry', 'INDUSTRY'),
                      ('faculty', 'ACADEMICIAN'), ('institution', 'INSTITUTION')]:
        user = User(key + '@example.com', 'password123', 'John', key, role=role)
        db.session.add(user)
        users[key] = user
    db.session.flush()
    profile = StudentProfile(user_id=users['student'].id, full_name='John Student')
    other = StudentProfile(user_id=users['other_student'].id, full_name='Other Student')
    python, sql = Skill('Python'), Skill('SQL')
    db.session.add_all([profile, other, python, sql])
    db.session.commit()
    headers = {key: {'Authorization': 'Bearer ' + create_access_token(identity=u)} for key, u in users.items()}
    body = {'title': 'Backend developer', 'description': 'Build web services', 'kind': 'JOB',
            'location': 'Chennai', 'employment_type': 'FULL_TIME', 'eligibility': 'CSE students',
            'deadline': (date.today() + timedelta(days=10)).isoformat(),
            'required_skills': [{'skill_id': python.id, 'weight': 3, 'required_proficiency': 40},
                                {'skill_id': sql.id, 'weight': 1, 'required_proficiency': 60}]}
    assert client.put('/api/industry/company', headers=headers['industry'], json={
        'name': 'Northstar Labs', 'description': 'Software company',
        'website': 'https://example.com', 'location': 'Chennai'}).status_code == 200
    response = client.post('/api/opportunities', headers=headers['industry'], json=body)
    assert response.status_code == 201, response.json
    application = client.post(f"/api/opportunities/{response.json['id']}/apply", headers=headers['student'])
    assert application.status_code == 201
    return {'h': headers, 'body': body, 'post': response.json['id'], 'application': application.json['id'],
            'student': profile.id, 'python': python.id, 'sql': sql.id}


def test_profile_posting_update_and_internship_fields(client, scenario):
    s = scenario
    h = s['h']['industry']
    company = client.get('/api/industry/company', headers=h).json
    assert company['website'] == 'https://example.com'
    assert client.get('/api/industry/company', headers=s['h']['other_industry']).json is None
    assert client.post('/api/opportunities', headers=s['h']['other_industry'], json=s['body']).status_code == 400
    body = deepcopy(s['body'])
    body.update(kind='INTERNSHIP', duration='12 weeks', stipend='INR 15000/month')
    body['required_skills'][0]['weight'] = 2
    response = client.put(f"/api/opportunities/{s['post']}", headers=h, json=body)
    assert response.status_code == 200, response.json
    for key in ('kind', 'duration', 'stipend', 'location', 'employment_type', 'eligibility', 'deadline'):
        assert response.json[key] == body[key]
    assert response.json['required_skills'][0]['weight'] == 2
    body['required_skills'] = body['required_skills'][1:]
    assert client.put(f"/api/opportunities/{s['post']}", headers=h, json=body).status_code == 200
    assert len(client.get(f"/api/opportunities/{s['post']}", headers=h).json['required_skills']) == 1
    assert client.get('/api/opportunities', headers=s['h']['other_industry']).json == []


@pytest.mark.parametrize('changes', [
    {'title': '   '}, {'description': '   '}, {'kind': 'UNKNOWN'}, {'company_id': 999},
    {'deadline': 'bad-date'}, {'deadline': (date.today() - timedelta(days=1)).isoformat()},
    {'required_skills': []}, {'required_skills': [{'skill_id': 99999, 'weight': 1, 'required_proficiency': 50}]},
    {'location': 'x' * 201}, {'employment_type': 'x' * 41}, {'duration': 'x' * 101},
])
def test_invalid_posting_rejected_without_mutation(client, scenario, changes):
    s = scenario
    body = {**s['body'], **changes}
    for method, path in [('POST', '/api/opportunities'), ('PUT', f"/api/opportunities/{s['post']}")]:
        assert client.open(path, method=method, headers=s['h']['industry'], json=body).status_code == 400
    assert Opportunity.query.count() == 1
    assert db.session.get(Opportunity, s['post']).title == s['body']['title']


@pytest.mark.parametrize('field,value', [('weight', 0), ('weight', -1), ('weight', 'NaN'),
    ('weight', 'Infinity'), ('required_proficiency', -1), ('required_proficiency', 101),
    ('required_proficiency', 'NaN'), ('skill_id', 1.5), ('skill_id', True)])
def test_invalid_requirement(client, scenario, field, value):
    body = deepcopy(scenario['body'])
    body['required_skills'][0][field] = value
    assert client.post('/api/opportunities', headers=scenario['h']['industry'], json=body).status_code == 400


def test_duplicate_skills_and_malformed_json(client, scenario):
    body = deepcopy(scenario['body'])
    body['required_skills'] *= 2
    assert client.post('/api/opportunities', headers=scenario['h']['industry'], json=body).status_code == 400
    for raw in ('null', '[]', '"text"', '{bad'):
        assert client.post('/api/opportunities', headers=scenario['h']['industry'],
                           data=raw, content_type='application/json').status_code == 400
    assert client.put('/api/industry/company', headers=scenario['h']['industry'], json={'name': '  '}).status_code == 400


@pytest.mark.parametrize('role', ['faculty', 'institution'])
def test_other_roles_denied_all_industry_opportunity_apis(client, scenario, role):
    s = scenario
    endpoints = [('GET', '/industry/company'), ('PUT', '/industry/company'), ('GET', '/industry/summary'),
                 ('GET', '/opportunities'), ('POST', '/opportunities'),
                 ('GET', f"/opportunities/{s['post']}"), ('PUT', f"/opportunities/{s['post']}"),
                 ('DELETE', f"/opportunities/{s['post']}"), ('POST', f"/opportunities/{s['post']}/apply"),
                 ('GET', f"/opportunities/{s['post']}/applications"), ('GET', '/applications/mine'),
                 ('GET', f"/applications/{s['application']}"), ('POST', f"/applications/{s['application']}/shortlist"),
                 ('PATCH', f"/applications/{s['application']}/status")]
    for method, path in endpoints:
        assert client.open('/api' + path, method=method, headers=s['h'][role], json={}).status_code == 403
        assert client.open('/api' + path, method=method, json={}).status_code == 401


def test_cross_owner_and_student_permissions(client, scenario):
    s = scenario
    for method, path in [('GET', f"/opportunities/{s['post']}"), ('PUT', f"/opportunities/{s['post']}"),
                         ('DELETE', f"/opportunities/{s['post']}"), ('GET', f"/opportunities/{s['post']}/applications"),
                         ('GET', f"/applications/{s['application']}"), ('POST', f"/applications/{s['application']}/shortlist"),
                         ('PATCH', f"/applications/{s['application']}/status")]:
        assert client.open('/api' + path, method=method, headers=s['h']['other_industry'], json={}).status_code == 403
        if not (method == 'GET' and path == f"/opportunities/{s['post']}"):
            assert client.open('/api' + path, method=method, headers=s['h']['student'], json={}).status_code == 403
    for method, path in [('PUT', '/industry/company'), ('GET', '/industry/company'),
                         ('POST', '/opportunities'), ('GET', '/industry/summary')]:
        assert client.open('/api' + path, method=method, headers=s['h']['student'], json={}).status_code == 403
    assert client.post(f"/api/opportunities/{s['post']}/apply", headers=s['h']['industry']).status_code == 403
    assert client.get('/api/applications/mine', headers=s['h']['industry']).status_code == 403
    assert client.get('/api/applications/mine', headers=s['h']['other_student']).json == []


def test_deadline_closure_and_tracking(client, scenario):
    s = scenario
    post = db.session.get(Opportunity, s['post'])
    post.deadline = date.today()
    db.session.commit()
    assert client.post(f"/api/opportunities/{s['post']}/apply", headers=s['h']['other_student']).status_code == 201
    assert client.post(f"/api/opportunities/{s['post']}/apply", headers=s['h']['student']).status_code == 409
    post.deadline = date.today() - timedelta(days=1)
    db.session.commit()
    assert client.get('/api/opportunities', headers=s['h']['student']).json == []
    assert client.get(f"/api/opportunities/{s['post']}", headers=s['h']['student']).status_code == 404
    assert client.post(f"/api/opportunities/{s['post']}/apply", headers=s['h']['student']).status_code == 404
    assert client.delete(f"/api/opportunities/{s['post']}", headers=s['h']['industry']).status_code == 204
    assert client.get('/api/applications/mine', headers=s['h']['student']).json[0]['status'] == 'APPLIED'
    assert len(client.get(f"/api/opportunities/{s['post']}/applications", headers=s['h']['industry']).json) == 2


def test_missing_profile_and_not_found(client, scenario):
    s = scenario
    user = User('no-profile@example.com', 'password123', 'John', 'Doe')
    db.session.add(user)
    db.session.commit()
    h = {'Authorization': 'Bearer ' + create_access_token(identity=user)}
    assert client.post(f"/api/opportunities/{s['post']}/apply", headers=h).status_code == 400
    assert client.get('/api/applications/mine', headers=h).json == []
    assert client.post('/api/opportunities/999999/apply', headers=h).status_code == 404
    assert client.get('/api/applications/999999', headers=s['h']['industry']).status_code == 404


def test_shortlist_tracking_transitions_and_final_status(client, scenario):
    s = scenario
    path = f"/api/applications/{s['application']}"
    h = s['h']['industry']
    assert client.post(path + '/shortlist', headers=h).json['status'] == 'SHORTLISTED'
    assert client.post(path + '/shortlist', headers=h).status_code == 200
    assert client.get('/api/applications/mine', headers=s['h']['student']).json[0]['status'] == 'SHORTLISTED'
    assert client.patch(path + '/status', headers=h, json={'status': 'UNKNOWN'}).status_code == 400
    assert client.patch(path + '/status', headers=h, json={'status': 'APPLIED'}).status_code == 409
    for status in ('INTERVIEW', 'OFFER'):
        assert client.patch(path + '/status', headers=h, json={'status': status}).json['status'] == status
    assert client.post(path + '/shortlist', headers=h).status_code == 409
    assert client.get('/api/industry/summary', headers=h).json['offers'] == 1
    second = client.post(f"/api/opportunities/{s['post']}/apply", headers=s['h']['other_student']).json['id']
    assert client.patch(f'/api/applications/{second}/status', headers=h, json={'status': 'REJECTED'}).json['status'] == 'REJECTED'
    assert client.post(f'/api/applications/{second}/shortlist', headers=h).status_code == 409


def test_matching_is_exact_phase3_output_with_real_evidence(client, scenario):
    s = scenario
    python = db.session.get(Skill, s['python'])
    db.session.add(StudentSkill(student_id=s['student'], skill_id=python.id, proficiency=ProficiencyLevel.ADVANCED))
    project = Project(s['student'], 'Python API', skills=[python], github_url='https://github.com/example/api')
    unrelated = Project(s['student'], 'Unrelated project')
    db.session.add_all([project, unrelated])
    db.session.flush()
    evidence = SkillEvidence(s['student'], python.id, 'PROJECT', 'API evidence', project_id=project.id,
                             source_url='https://example.com/evidence')
    db.session.add(evidence)
    role = Role(name='Reference role')
    role.requirements = [RoleSkillRequirement(**item) for item in s['body']['required_skills']]
    db.session.add(role)
    db.session.commit()
    expected = SkillIntelligenceService.analyze_role(s['student'], role)
    counts = (Role.query.count(), RoleSkillRequirement.query.count())
    with patch.object(SkillIntelligenceService, 'analyze_role', wraps=SkillIntelligenceService.analyze_role) as matcher:
        response = client.get(f"/api/applications/{s['application']}", headers=s['h']['industry'])
        assert response.status_code == 200
        assert matcher.call_count == 1
    actual = response.json['match']
    for key in ('match_percentage', 'required_skills', 'skill_gaps', 'missing_skills'):
        assert actual[key] == expected[key]
    assert [row['skill'] for row in actual['matching_skills']] == ['Python']
    assert actual['missing_skills'] == ['SQL']
    assert actual['evidence'][0]['source_url'] == evidence.source_url
    assert actual['evidence'][0]['evidence_title'] == 'API evidence'
    assert [p['id'] for p in actual['relevant_projects']] == [project.id]
    assert client.get(f"/api/applications/{s['application']}", headers=s['h']['industry']).json['match'] == actual
    assert (Role.query.count(), RoleSkillRequirement.query.count()) == counts
    assert 'password_hash' not in response.get_data(as_text=True)


def test_empty_candidate_has_zero_score_and_missing_skills(client, scenario):
    result = client.get(f"/api/applications/{scenario['application']}", headers=scenario['h']['industry']).json['match']
    assert result['match_percentage'] == 0
    assert set(result['missing_skills']) == {'Python', 'SQL'}
    assert result['matching_skills'] == result['evidence'] == result['relevant_projects'] == []


def test_database_prevents_duplicate_applications(scenario):
    db.session.add(OpportunityApplication(opportunity_id=scenario['post'], student_id=scenario['student']))
    with pytest.raises(IntegrityError):
        db.session.commit()
    db.session.rollback()
    assert OpportunityApplication.query.count() == 1
