"""Student profile service for business logic."""
from app.extensions import db
from app.models.user import User
from app.models.student_profile import StudentProfile


class StudentProfileService:
    """Service layer for student profile operations."""

    @staticmethod
    def get_profile(user_id: int) -> StudentProfile:
        """Get student profile by user ID."""
        return StudentProfile.query.filter_by(user_id=user_id).first()

    @staticmethod
    def create_or_update_profile(user_id: int, data: dict) -> StudentProfile:
        """Create or update student profile for a user."""
        # Verify user exists and is a student
        user = User.query.filter_by(id=user_id, is_active=True).first()
        if not user:
            raise ValueError("User not found")
        if not user.has_role("STUDENT"):
            raise ValueError("Only students can have a student profile")

        profile = StudentProfile.query.filter_by(user_id=user_id).first()

        if profile:
            # Update existing profile
            for key, value in data.items():
                if hasattr(profile, key) and key not in ("id", "user_id", "created_at"):
                    setattr(profile, key, value)
        else:
            # Create new profile
            profile = StudentProfile(user_id=user_id, **data)
            db.session.add(profile)

        db.session.commit()
        return profile

    @staticmethod
    def delete_profile(user_id: int) -> bool:
        """Delete student profile for a user."""
        profile = StudentProfile.query.filter_by(user_id=user_id).first()
        if not profile:
            return False
        db.session.delete(profile)
        db.session.commit()
        return True