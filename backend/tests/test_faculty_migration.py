"""Exercise migrated existing records, including their legacy timestamp format."""
import os
from pathlib import Path
import subprocess
import sys


def test_existing_project_can_be_reviewed_after_migration(tmp_path):
    backend = Path(__file__).resolve().parents[1]
    script = r'''
from app import create_app
from app.extensions import db
from sqlalchemy import text
from werkzeug.security import generate_password_hash
from app.models.faculty import FacultyProfile
app = create_app('development')
runner = app.test_cli_runner()
result = runner.invoke(args=['db', 'upgrade', '9d2af314f0c1'])
assert result.exit_code == 0, result.output
with app.app_context():
    for uid, email, role in [(1, 'student@example.com', 'STUDENT'), (2, 'faculty@example.com', 'ACADEMICIAN')]:
        db.session.execute(text("INSERT INTO users (id,email,password_hash,first_name,last_name,role,is_active,created_at,updated_at) VALUES (:id,:email,:password,'Test','User',:role,1,CURRENT_TIMESTAMP,CURRENT_TIMESTAMP)"), dict(id=uid,email=email,password=generate_password_hash('password123'),role=role))
    db.session.execute(text("INSERT INTO student_profiles (id,user_id,full_name,institution,created_at,updated_at) VALUES (1,1,'Existing Student','Test University',CURRENT_TIMESTAMP,CURRENT_TIMESTAMP)"))
    db.session.execute(text("INSERT INTO projects (id,student_id,title,description,created_at,updated_at) VALUES (1,1,'Existing project','Existing portfolio data',CURRENT_TIMESTAMP,CURRENT_TIMESTAMP)"))
    db.session.commit()
result = runner.invoke(args=['db', 'upgrade'])
assert result.exit_code == 0, result.output
result = runner.invoke(args=['db', 'upgrade'])
assert result.exit_code == 0, result.output
with app.app_context():
    db.session.add(FacultyProfile(user_id=2,institution='Test University'))
    db.session.commit()
client = app.test_client()
login = client.post('/api/auth/login', json={'email':'faculty@example.com','password':'password123'})
assert login.status_code == 200, login.get_json()
headers = {'Authorization':'Bearer '+login.get_json()['access_token']}
reviews = client.get('/api/faculty/reviews?status=PENDING',headers=headers).get_json()
assert len(reviews) == 1
review = reviews[0]
assert review['project']['description'] == 'Existing portfolio data'
result = client.post('/api/faculty/reviews/'+str(review['id'])+'/decision',headers=headers,
                     json={'decision':'APPROVED','expected_updated_at':review['updated_at']})
assert result.status_code == 200, result.get_json()
assert result.get_json()['project']['verification_status'] == 'APPROVED'
assert client.get('/api/faculty/students/1',headers=headers).get_json()['endorsements']['has_endorsements']
'''
    env = {**os.environ, 'DATABASE_URL': f"sqlite:///{tmp_path / 'faculty-migration.db'}", 'FLASK_ENV':'development'}
    result = subprocess.run([sys.executable, '-c', script], cwd=backend, env=env, capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr
