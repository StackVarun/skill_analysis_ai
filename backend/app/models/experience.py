"""Experience model."""
import enum
from datetime import datetime, timezone
from app.extensions import db
from app.models.student_profile import StudentProfile
from app.models.skill import Skill


class EmploymentType(str, enum.Enum):
    """Employment types for experience."""
    INTERNSHIP = "INTERNSHIP"
    FULL_TIME = "FULL_TIME"
    PART_TIME = "PART_TIME"
    FREELANCE = "FREELANCE"
    OTHER = "OTHER"

    @classmethod
    def list(cls):
        return [e.value for e in cls]


class Experience(db.Model):
    """Experience database model."""
    __tablename__ = "experiences"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    student_id = db.Column(db.Integer, db.ForeignKey("student_profiles.id", ondelete="CASCADE"), nullable=False, index=True)

    organization = db.Column(db.String(200), nullable=False)
    job_title = db.Column(db.String(200), nullable=False)
    employment_type = db.Column(
        db.Enum(EmploymentType, name="employment_types", native_enum=False, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        default=EmploymentType.FULL_TIME
    )
    location = db.Column(db.String(200), nullable=True)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=True)
    description = db.Column(db.Text, nullable=True)

    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    student = db.relationship("StudentProfile", backref=db.backref("experiences", cascade="all, delete-orphan"))
    skills = db.relationship("Skill", secondary="experience_skills", backref=db.backref("experiences", lazy="dynamic"))

    def __init__(self, student_id: int, organization: str, job_title: str, start_date, **kwargs):
        self.student_id = student_id
        self.organization = organization.strip()
        self.job_title = job_title.strip()
        self.start_date = start_date
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)

    def to_dict(self) -> dict:
        """Serialize experience to dictionary."""
        emp_type = self.employment_type.value if isinstance(self.employment_type, EmploymentType) else str(self.employment_type)
        return {
            "id": self.id,
            "student_id": self.student_id,
            "organization": self.organization,
            "job_title": self.job_title,
            "employment_type": emp_type,
            "location": self.location,
            "start_date": self.start_date.isoformat() if self.start_date else None,
            "end_date": self.end_date.isoformat() if self.end_date else None,
            "description": self.description,
            "skills": [{"id": s.id, "name": s.name, "category": s.category} for s in self.skills],
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def __repr__(self) -> str:
        return f"<Experience {self.id}: {self.job_title} at {self.organization}>"


# Association table for experience-skills many-to-many relationship
experience_skills = db.Table(
    "experience_skills",
    db.Column("experience_id", db.Integer, db.ForeignKey("experiences.id", ondelete="CASCADE"), primary_key=True),
    db.Column("skill_id", db.Integer, db.ForeignKey("skills.id", ondelete="CASCADE"), primary_key=True)
)