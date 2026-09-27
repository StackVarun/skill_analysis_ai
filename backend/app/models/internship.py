"""Internship model."""
import enum
from datetime import datetime, timezone
from app.extensions import db
from app.models.student_profile import StudentProfile
from app.models.skill import Skill


class InternshipType(str, enum.Enum):
    """Internship types."""
    SUMMER = "SUMMER"
    WINTER = "WINTER"
    PART_TIME = "PART_TIME"
    FULL_TIME = "FULL_TIME"
    REMOTE = "REMOTE"
    OTHER = "OTHER"

    @classmethod
    def list(cls):
        return [e.value for e in cls]


class InternshipStatus(str, enum.Enum):
    """Internship status."""
    COMPLETED = "COMPLETED"
    ONGOING = "ONGOING"
    PLANNED = "PLANNED"
    CANCELLED = "CANCELLED"

    @classmethod
    def list(cls):
        return [e.value for e in cls]


class Internship(db.Model):
    """Internship database model."""
    __tablename__ = "internships"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    student_id = db.Column(db.Integer, db.ForeignKey("student_profiles.id", ondelete="CASCADE"), nullable=False, index=True)

    organization = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(200), nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=True)
    description = db.Column(db.Text, nullable=True)
    certificate_url = db.Column(db.String(500), nullable=True)
    internship_type = db.Column(
        db.Enum(InternshipType, name="internship_types", native_enum=False, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        default=InternshipType.SUMMER
    )
    status = db.Column(
        db.Enum(InternshipStatus, name="internship_statuses", native_enum=False, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        default=InternshipStatus.COMPLETED
    )

    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    student = db.relationship("StudentProfile", backref=db.backref("internships", cascade="all, delete-orphan"))
    skills = db.relationship("Skill", secondary="internship_skills", backref=db.backref("internships", lazy="dynamic"))

    def __init__(self, student_id: int, organization: str, role: str, start_date, **kwargs):
        self.student_id = student_id
        self.organization = organization.strip()
        self.role = role.strip()
        self.start_date = start_date
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)

    def to_dict(self) -> dict:
        """Serialize internship to dictionary."""
        internship_type = self.internship_type.value if isinstance(self.internship_type, InternshipType) else str(self.internship_type)
        status = self.status.value if isinstance(self.status, InternshipStatus) else str(self.status)
        return {
            "id": self.id,
            "student_id": self.student_id,
            "organization": self.organization,
            "role": self.role,
            "start_date": self.start_date.isoformat() if self.start_date else None,
            "end_date": self.end_date.isoformat() if self.end_date else None,
            "description": self.description,
            "certificate_url": self.certificate_url,
            "internship_type": internship_type,
            "status": status,
            "skills": [{"id": s.id, "name": s.name, "category": s.category} for s in self.skills],
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def __repr__(self) -> str:
        return f"<Internship {self.id}: {self.role} at {self.organization}>"


# Association table for internship-skills many-to-many relationship
internship_skills = db.Table(
    "internship_skills",
    db.Column("internship_id", db.Integer, db.ForeignKey("internships.id", ondelete="CASCADE"), primary_key=True),
    db.Column("skill_id", db.Integer, db.ForeignKey("skills.id", ondelete="CASCADE"), primary_key=True)
)