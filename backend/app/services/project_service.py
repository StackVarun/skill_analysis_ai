"""Project service for business logic."""
from app.extensions import db
from app.models.student_profile import StudentProfile
from app.models.project import Project
from app.models.skill import Skill


def catalog_skills(ids):
    if len(ids) != len(set(ids)):
        raise ValueError("Duplicate project skill")
    skills = Skill.query.filter(Skill.id.in_(ids)).all()
    if len(skills) != len(ids):
        raise ValueError("Unknown project skill")
    return skills


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
                       start_date = None, end_date = None, role: str = None, skill_ids: list = None, completion_status: str = "COMPLETED") -> Project:
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
            role=role,
            completion_status=completion_status
        )

        # Associate skills if provided
        if skill_ids:
            skills = catalog_skills(skill_ids)
            project.skills = skills

        db.session.add(project)
        db.session.flush()
        from app.services.faculty_support_service import project_changed
        project_changed(project)
        db.session.commit()
        return project

    @staticmethod
    def update_project(project_id: int, student_id: int, data: dict) -> Project:
        """Update a student's project."""
        project = Project.query.filter_by(id=project_id, student_id=student_id).first()
        if not project:
            raise ValueError("Project not found")

        selected_skills = catalog_skills(data["skill_ids"]) if "skill_ids" in data else None
        before = project.to_dict()
        for key, value in data.items():
            if key == "skill_ids":
                if value is not None:
                    project.skills = selected_skills
            elif hasattr(project, key) and key not in ("id", "student_id", "created_at"):
                setattr(project, key, value)

        db.session.flush()
        after = project.to_dict()
        if any(before[k] != after[k] for k in ("title", "description", "technologies", "project_url", "github_url", "start_date", "end_date", "role", "skills", "completion_status")):
            from app.services.faculty_support_service import project_changed
            project_changed(project)
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