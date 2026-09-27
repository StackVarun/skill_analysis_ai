"""Routes package initialization."""
from app.routes.auth_routes import auth_bp
from app.routes.test_routes import test_bp
from app.routes.student_routes import student_bp
from app.routes.skill_routes import skills_bp
from app.routes.student_skill_routes import student_skills_bp
from app.routes.project_routes import projects_bp
from app.routes.certification_routes import certifications_bp
from app.routes.experience_routes import experiences_bp
from app.routes.internship_routes import internships_bp
from app.routes.skill_evidence_routes import skill_evidence_bp
from app.routes.resume_routes import resumes_bp

__all__ = ["auth_bp", "test_bp", "student_bp", "skills_bp", "student_skills_bp", "projects_bp", "certifications_bp", "experiences_bp", "internships_bp", "skill_evidence_bp", "resumes_bp"]