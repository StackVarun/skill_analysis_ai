"""Test configuration and fixtures."""
import os
import sys
import pytest
from datetime import date

# Add backend to path
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, backend_dir)

from app import create_app
from app.extensions import db
from app.models.user import User
from app.models.student_profile import StudentProfile
from app.models.skill import Skill
from app.models.student_skill import StudentSkill, ProficiencyLevel
from app.models.project import Project
from app.models.certification import Certification
from app.models.experience import Experience, EmploymentType
from app.models.internship import Internship, InternshipType, InternshipStatus
from app.models.skill_evidence import SkillEvidence, EvidenceType, VerificationStatus
from app.models.resume import Resume, ResumeStatus
from app.services.auth_service import AuthService


@pytest.fixture
def app():
    """Create test app."""
    app = create_app("testing")
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()


@pytest.fixture
def client(app):
    """Create test client."""
    return app.test_client()


@pytest.fixture
def student_user_id(app):
    """Create a test student user and return ID."""
    with app.app_context():
        user = AuthService.register_user(
            email="student@test.com",
            password="password123",
            first_name="Test",
            last_name="Student",
            role="STUDENT"
        )
        return user.id


@pytest.fixture
def industry_user_id(app):
    """Create a test industry user and return ID."""
    with app.app_context():
        user = AuthService.register_user(
            email="industry@test.com",
            password="password123",
            first_name="Test",
            last_name="Industry",
            role="INDUSTRY"
        )
        return user.id


@pytest.fixture
def auth_headers(app, student_user_id):
    """Get auth headers for student user."""
    with app.app_context():
        from flask_jwt_extended import create_access_token
        user = User.query.filter_by(id=student_user_id).first()
        token = create_access_token(identity=user)
        return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def industry_auth_headers(app, industry_user_id):
    """Get auth headers for industry user."""
    with app.app_context():
        from flask_jwt_extended import create_access_token
        user = User.query.filter_by(id=industry_user_id).first()
        token = create_access_token(identity=user)
        return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def student_profile_id(app, student_user_id):
    """Create a student profile and return ID."""
    with app.app_context():
        profile = StudentProfile.query.filter_by(user_id=student_user_id).first()
        if profile is None:
            profile = StudentProfile(user_id=student_user_id)
            db.session.add(profile)
            db.session.commit()
        return profile.id


@pytest.fixture
def skill_id(app):
    """Create a test skill and return ID."""
    with app.app_context():
        skill = Skill(name="Python", category="Programming", description="Python programming language")
        db.session.add(skill)
        db.session.commit()
        return skill.id
