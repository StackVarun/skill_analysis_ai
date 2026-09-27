"""Student skill association model."""
import enum
from datetime import datetime, timezone
from app.extensions import db
from app.models.student_profile import StudentProfile
from app.models.skill import Skill


class ProficiencyLevel(str, enum.Enum):
    """Proficiency levels for student skills."""
    BEGINNER = "BEGINNER"
    INTERMEDIATE = "INTERMEDIATE"
    ADVANCED = "ADVANCED"
    EXPERT = "EXPERT"

    @classmethod
    def list(cls):
        return [level.value for level in cls]


class StudentSkill(db.Model):
    """Student-Skill association model with proficiency and evidence."""
    __tablename__ = "student_skills"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    student_id = db.Column(db.Integer, db.ForeignKey("student_profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    skill_id = db.Column(db.Integer, db.ForeignKey("skills.id", ondelete="CASCADE"), nullable=False, index=True)

    proficiency = db.Column(
        db.Enum(ProficiencyLevel, name="proficiency_levels", native_enum=False, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        default=ProficiencyLevel.BEGINNER
    )
    years_experience = db.Column(db.Integer, nullable=True)
    months_experience = db.Column(db.Integer, nullable=True)
    source = db.Column(db.String(200), nullable=True)

    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    # Relationships
    student = db.relationship("StudentProfile", backref=db.backref("skills", cascade="all, delete-orphan"))
    skill = db.relationship("Skill", backref=db.backref("students", cascade="all, delete-orphan"))

    # Unique constraint to prevent duplicate student-skill relationships
    __table_args__ = (
        db.UniqueConstraint("student_id", "skill_id", name="uq_student_skill"),
    )

    def __init__(self, student_id: int, skill_id: int, proficiency: str = "BEGINNER",
                 years_experience: int = None, months_experience: int = None, source: str = None):
        self.student_id = student_id
        self.skill_id = skill_id
        if isinstance(proficiency, str):
            self.proficiency = ProficiencyLevel(proficiency.upper())
        else:
            self.proficiency = proficiency
        self.years_experience = years_experience
        self.months_experience = months_experience
        self.source = source.strip() if source else None

    def to_dict(self) -> dict:
        """Serialize student skill to dictionary."""
        proficiency_val = self.proficiency.value if isinstance(self.proficiency, ProficiencyLevel) else str(self.proficiency)
        return {
            "id": self.id,
            "student_id": self.student_id,
            "skill_id": self.skill_id,
            "skill_name": self.skill.name if self.skill else None,
            "skill_category": self.skill.category if self.skill else None,
            "proficiency": proficiency_val,
            "years_experience": self.years_experience,
            "months_experience": self.months_experience,
            "source": self.source,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def __repr__(self) -> str:
        return f"<StudentSkill {self.id}: student={self.student_id}, skill={self.skill_id}>"