"""Project service for business logic."""
from app.extensions import db
from app.models.student_profile import StudentProfile
from app.models.project import Project
from app.models.skill import Skill


class ProjectService:
    """Service layer for project operations."""

    @staticmethod
    def get_student_projects(student_id: int):
        """Get all projects for a student."""
        return Project.query.filter_by(student_id=student_id).order_by(Project.created_at.desc()).all()

    @staticmethod
    def get_project_by_id(project_id: int):
        """Get project by ID."""
        return Project.query.filter_by(id=project_id).first()

    @staticmethod
    def get_student_project(student_id: int, project_id: int):
        """Get a specific student's project."""
        return Project.query.filter_by(student_id=student_id, id=project_id).first()

    @staticmethod
    def create_project(student_id: int, title: str, description: str = None,
                       technologies: str = None, project_url: str = None, github_url: str = None,
                       start_date = None, end_date = None, role: str = None, skill_ids: list = None) -> Project:
        """Create a new project for a student."""
        # Verify student profile exists
        student = StudentProfile.query.filter_by(id=student_id).first()
        if not student:
            raise ValueError("Student profile not found")

        project = Project(
            student_id=student_id,
            title=title,
            description=description,
            technologies=technologies,
            project_url=project_url,
            github_url=github_url,
            start_date=start_date,
            end_date=end_date,
            role=role
        )

        # Associate skills if provided
        if skill_ids:
            skills = Skill.query.filter(Skill.id.in_(skill_ids)).all()
            project.skills = skills

        db.session.add(project)
        db.session.commit()
        return project

    @staticmethod
    def update_project(project_id: int, student_id: int, data: dict) -> Project:
        """Update a student's project."""
        project = Project.query.filter_by(id=project_id, student_id=student_id).first()
        if not project:
            raise ValueError("Project not found")

        for key, value in data.items():
            if key == "skill_ids":
                if value is not None:
                    skills = Skill.query.filter(Skill.id.in_(value)).all()
                    project.skills = skills
            elif hasattr(project, key) and key not in ("id", "student_id", "created_at"):
                setattr(project, key, value)

        db.session.commit()
        return project

    @staticmethod
    def delete_project(project_id: int, student_id: int) -> bool:
        """Delete a student's project."""
        project = Project.query.filter_by(id=project_id, student_id=student_id).first()
        if not project:
            return False
        db.session.delete(project)
        db.session.commit()
        return True