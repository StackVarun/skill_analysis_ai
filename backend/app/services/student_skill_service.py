"""Student skill service for business logic."""
from app.extensions import db
from app.models.student_profile import StudentProfile
from app.models.skill import Skill
from app.models.student_skill import StudentSkill, ProficiencyLevel


class StudentSkillService:
    """Service layer for student skill operations."""

    @staticmethod
    def get_student_skills(student_id: int):
        """Get all skills for a student."""
        return StudentSkill.query.filter_by(student_id=student_id).all()

    @staticmethod
    def get_student_skill(student_id: int, skill_id: int):
        """Get a specific student skill."""
        return StudentSkill.query.filter_by(student_id=student_id, skill_id=skill_id).first()

    @staticmethod
    def add_skill(student_id: int, skill_id: int, proficiency: str = "BEGINNER",
                  years_experience: int = None, months_experience: int = None, source: str = None) -> StudentSkill:
        """Add a skill to a student's profile."""
        # Verify student profile exists
        student = StudentProfile.query.filter_by(id=student_id).first()
        if not student:
            raise ValueError("Student profile not found")

        # Verify skill exists
        skill = Skill.query.filter_by(id=skill_id).first()
        if not skill:
            raise ValueError("Skill not found")

        # Check for duplicate
        existing = StudentSkill.query.filter_by(student_id=student_id, skill_id=skill_id).first()
        if existing:
            raise ValueError("Student already has this skill")

        # Validate proficiency
        try:
            prof = ProficiencyLevel(proficiency.upper())
        except ValueError:
            raise ValueError(f"Invalid proficiency. Must be one of: {', '.join(ProficiencyLevel.list())}")

        student_skill = StudentSkill(
            student_id=student_id,
            skill_id=skill_id,
            proficiency=prof,
            years_experience=years_experience,
            months_experience=months_experience,
            source=source
        )
        db.session.add(student_skill)
        db.session.commit()
        return student_skill

    @staticmethod
    def update_skill(student_id: int, skill_id: int, data: dict) -> StudentSkill:
        """Update a student's skill proficiency."""
        student_skill = StudentSkill.query.filter_by(student_id=student_id, skill_id=skill_id).first()
        if not student_skill:
            raise ValueError("Student skill not found")

        if "proficiency" in data:
            try:
                student_skill.proficiency = ProficiencyLevel(data["proficiency"].upper())
            except ValueError:
                raise ValueError(f"Invalid proficiency. Must be one of: {', '.join(ProficiencyLevel.list())}")

        if "years_experience" in data:
            student_skill.years_experience = data["years_experience"]

        if "months_experience" in data:
            student_skill.months_experience = data["months_experience"]

        if "source" in data:
            student_skill.source = data["source"]

        db.session.commit()
        return student_skill

    @staticmethod
    def remove_skill(student_id: int, skill_id: int) -> bool:
        """Remove a skill from a student's profile."""
        student_skill = StudentSkill.query.filter_by(student_id=student_id, skill_id=skill_id).first()
        if not student_skill:
            return False
        db.session.delete(student_skill)
        db.session.commit()
        return True