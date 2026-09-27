"""Enumerations for SkillBridge AI models."""
import enum


class UserRole(str, enum.Enum):
    """User roles for role-based access control."""
    STUDENT = "STUDENT"
    INDUSTRY = "INDUSTRY"
    ACADEMICIAN = "ACADEMICIAN"
    INSTITUTION = "INSTITUTION"

    @classmethod
    def list(cls):
        """Return list of valid role values."""
        return [role.value for role in cls]
