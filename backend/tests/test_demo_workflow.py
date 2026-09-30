"""End-to-end checks of login, demo applicants, ranking, and safe reruns."""
from app.extensions import db
from app.models.user import User
from app.models.opportunity import Opportunity, CompanyProfile, OpportunitySkill, OpportunityApplication
from app.models.skill import Skill
from app.models.project import Project
from app.models.skill_evidence import SkillEvidence
from seed_demo import seed_demo, STUDENTS

PASSWORD = 'DemoPass123!'


def login(client, email, password=PASSWORD):
    response = client.post('/api/auth/login', json={'email': email, 'password': password})
    assert response.status_code == 200, response.get_json()
    return {'Authorization': f"Bearer {response.get_json()['access_token']}"}


def test_demo_logins_five_applicants_and_ranking(app, client):
    with app.app_context():
        post, profiles = seed_demo(PASSWORD)
        post_id = post.id
        before = (User.query.count(), Project.query.count(), SkillEvidence.query.count())
        seed_demo(PASSWORD)
        assert before == (User.query.count(), Project.query.count(), SkillEvidence.query.count())
        assert OpportunityApplication.query.count() == 5
    for email in ['student@demo.skillbridge', 'faculty@demo.skillbridge', 'institution@demo.skillbridge']:
        login(client, email)
    industry = login(client, 'industry@demo.skillbridge')
    for email, *_ in STUDENTS:
        student = login(client, email)
        mine = client.get('/api/applications/mine', headers=student).get_json()
        assert len(mine) == 1 and mine[0]['opportunity_id'] == post_id
        assert client.post(f'/api/opportunities/{post_id}/apply', headers=student).status_code == 409
    result = client.get(f'/api/opportunities/{post_id}/applications', headers=industry)
    assert result.status_code == 200
    rows = result.get_json()
    scores = [r['match']['match_percentage'] for r in rows]
    assert scores == [90, 65, 50, 40, 15]
    assert all(e['status'] == 'SELF_REPORTED' for r in rows for e in r['match']['evidence'])
    assert rows[0]['student']['full_name'] == 'John Doe'
    assert not rows[0]['match']['skill_gaps']
    assert rows[-1]['match']['skill_gaps']
    best = rows[0]['id']
    assert client.post(f'/api/applications/{best}/shortlist', headers=industry).get_json()['status'] == 'SHORTLISTED'
    # Industry can create catalog skills; student access remains restricted.
    assert client.post('/api/skills', json={'name': 'FastAPI'}, headers=industry).status_code == 201
    assert client.post('/api/skills', json={'name': 'Another skill'}, headers=student).status_code == 403


def test_password_reset_is_explicit_and_scoped(app, client):
    with app.app_context():
        seed_demo('old-password')
        unrelated = User('other@example.com', 'unchanged-password', 'Other', 'User', 'STUDENT')
        db.session.add(unrelated)
        db.session.commit()
        seed_demo(PASSWORD)
    assert client.post('/api/auth/login', json={'email': 'student@demo.skillbridge', 'password': PASSWORD}).status_code == 401
    with app.app_context():
        seed_demo(PASSWORD, reset_passwords=True)
    login(client, 'student@demo.skillbridge')
    login(client, 'student1@test.com')
    login(client, 'other@example.com', 'unchanged-password')


def test_seed_reuses_existing_job_and_preserves_owner_requirements(app, client):
    with app.app_context():
        owner = User('owner@example.com', PASSWORD, 'Job', 'Owner', 'INDUSTRY')
        skill = Skill('Java')
        db.session.add_all([owner, skill]); db.session.flush()
        company = CompanyProfile(user_id=owner.id, name='Existing Company')
        db.session.add(company); db.session.flush()
        post = Opportunity(company_id=company.id, title='Existing Job', kind='JOB', description='Java developer')
        post.requirements = [OpportunitySkill(skill_id=skill.id, required_proficiency=80, weight=3)]
        db.session.add(post); db.session.commit()
        post_id = post.id
        selected, _ = seed_demo(PASSWORD)
        assert selected.id == post_id
        assert Opportunity.query.count() == 1
        assert selected.company.user_id == owner.id
        assert selected.requirements[0].required_proficiency == 80
        assert len(selected.applications) == 5
        seed_demo(PASSWORD, opportunity_id=post_id)
        assert OpportunityApplication.query.count() == 5
    rows = client.get(f'/api/opportunities/{post_id}/applications', headers=login(client, 'owner@example.com'))
    assert len(rows.get_json()) == 5
    assert client.get(f'/api/opportunities/{post_id}/applications', headers=login(client, 'industry@demo.skillbridge')).status_code == 403
