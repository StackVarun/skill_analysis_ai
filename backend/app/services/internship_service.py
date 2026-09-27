"""Internship service for business logic."""
from app.extensions import db
from app.models.student_profile import StudentProfile
from app.models.internship import Internship, InternshipType, InternshipStatus
from app.models.skill import Skill


class InternshipService:
    """Service layer for internship operations."""

    @staticmethod
    def get_student_internships(student_id: int):
        """Get all internships for a student."""
        return Internship.query.filter_by(student_id=student_id).order_by(Internship.start_date.desc()).all()

    @staticmethod
    def get_internship_by_id(internship_id: int):
        """Get internship by ID."""
        return Internship.query.filter_by(id=internship_id).first()

    @staticmethod
    def get_student_internship(student_id: int, internship_id: int):
        """Get a specific student's internship."""
        return Internship.query.filter_by(student_id=student_id, id=internship_id).first()

    @staticmethod
    def create_internship(student_id: int, organization: str, role: str, start_date,
                          end_date=None, description=None, certificate_url=None,
                          internship_type: str = "SUMMER", status: str = "COMPLETED",
                          skill_ids=None) -> Internship:
        """Create a new internship for a student."""
        student = StudentProfile.query.filter_by(id=student_id).first()
        if not student:
            raise ValueError("Student profile not found")

        try:
            int_type = InternshipType(internship_type.upper())
        except ValueError:
            raise ValueError(f"Invalid internship type. Must be one of: {', '.join(InternshipType.list())}")

        try:
            int_status = InternshipStatus(status.upper())
        except ValueError:
            raise ValueError(f"Invalid status. Must be one of: {', '.join(InternshipStatus.list())}")

        internship = Internship(
            student_id=student_id,
            organization=organization,
            role=role,
            start_date=start_date,
            end_date=end_date,
            description=description,
            certificate_url=certificate_url,
            internship_type=int_type,
            status=int_status
        )

        if skill_ids:
            skills = Skill.query.filter(Skill.id.in_(skill_ids)).all()
            internship.skills = skills

        db.session.add(internship)
        db.session.commit()
        return internship

    @staticmethod
    def update_internship(internship_id: int, student_id: int, data: dict) -> Internship:
        """Update a student's internship."""
        internship = Internship.query.filter_by(id=internship_id, student_id=student_id).first()
        if not internship:
            raise ValueError("Internship not found")

        if "internship_type" in data and data["internship_type"]:
            try:
                internship.internship_type = InternshipType(data["internship_type"].upper())
            except ValueError:
                raise ValueError(f"Invalid internship type. Must be one of: {', '.join(InternshipType.list())}")

        if "status" in data and data["status"]:
            try:
                internship.status = InternshipStatus(data["status"].upper())
            except ValueError:
                raise ValueError(f"Invalid status. Must be one of: {', '.join(InternshipStatus.list())}")

        if "skill_ids" in data:
            if data["skill_ids"] is not None:
                skills = Skill.query.filter(Skill.id.in_(data["skill_ids"])).all()
                internship.skills = skills
        else:
            for key, value in data.items():
                if hasattr(internship, key) and key not in ("id", "student_id", "created_at", "skill_ids"):
                    setattr(internship, key, value)

        db.session.commit()
        return internship

    @staticmethod
    def delete_internship(internship_id: int, student_id: int) -> bool:
        """Delete a student's internship."""
        internship = Internship.query.filter_by(id=internship_id, student_id=student_id).first()
        if not internship:
            return False
        db.session.delete(internship)
        db.session.commit()
        return True