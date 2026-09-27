"""Experience service for business logic."""
from app.extensions import db
from app.models.student_profile import StudentProfile
from app.models.experience import Experience, EmploymentType
from app.models.skill import Skill


class ExperienceService:
    """Service layer for experience operations."""

    @staticmethod
    def get_student_experiences(student_id: int):
        """Get all experiences for a student."""
        return Experience.query.filter_by(student_id=student_id).order_by(Experience.start_date.desc()).all()

    @staticmethod
    def get_experience_by_id(exp_id: int):
        """Get experience by ID."""
        return Experience.query.filter_by(id=exp_id).first()

    @staticmethod
    def get_student_experience(student_id: int, exp_id: int):
        """Get a specific student's experience."""
        return Experience.query.filter_by(student_id=student_id, id=exp_id).first()

    @staticmethod
    def create_experience(student_id: int, organization: str, job_title: str, start_date,
                          employment_type: str = "FULL_TIME", location=None, end_date=None,
                          description=None, skill_ids=None) -> Experience:
        """Create a new experience for a student."""
        student = StudentProfile.query.filter_by(id=student_id).first()
        if not student:
            raise ValueError("Student profile not found")

        # Validate employment type
        try:
            emp_type = EmploymentType(employment_type.upper())
        except ValueError:
            raise ValueError(f"Invalid employment type. Must be one of: {', '.join(EmploymentType.list())}")

        exp = Experience(
            student_id=student_id,
            organization=organization,
            job_title=job_title,
            employment_type=emp_type,
            location=location,
            start_date=start_date,
            end_date=end_date,
            description=description
        )

        if skill_ids:
            skills = Skill.query.filter(Skill.id.in_(skill_ids)).all()
            exp.skills = skills

        db.session.add(exp)
        db.session.commit()
        return exp

    @staticmethod
    def update_experience(exp_id: int, student_id: int, data: dict) -> Experience:
        """Update a student's experience."""
        exp = Experience.query.filter_by(id=exp_id, student_id=student_id).first()
        if not exp:
            raise ValueError("Experience not found")

        if "employment_type" in data and data["employment_type"]:
            try:
                exp.employment_type = EmploymentType(data["employment_type"].upper())
            except ValueError:
                raise ValueError(f"Invalid employment type. Must be one of: {', '.join(EmploymentType.list())}")

        if "skill_ids" in data:
            if data["skill_ids"] is not None:
                skills = Skill.query.filter(Skill.id.in_(data["skill_ids"])).all()
                exp.skills = skills
        else:
            for key, value in data.items():
                if hasattr(exp, key) and key not in ("id", "student_id", "created_at", "skill_ids"):
                    setattr(exp, key, value)

        db.session.commit()
        return exp

    @staticmethod
    def delete_experience(exp_id: int, student_id: int) -> bool:
        """Delete a student's experience."""
        exp = Experience.query.filter_by(id=exp_id, student_id=student_id).first()
        if not exp:
            return False
        db.session.delete(exp)
        db.session.commit()
        return True