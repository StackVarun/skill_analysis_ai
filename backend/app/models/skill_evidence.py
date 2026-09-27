"""Skill evidence model."""
import enum
from datetime import datetime, timezone
from app.extensions import db
from app.models.student_profile import StudentProfile
from app.models.skill import Skill
from app.models.project import Project
from app.models.certification import Certification
from app.models.experience import Experience
from app.models.internship import Internship


class EvidenceType(str, enum.Enum):
    """Evidence types."""
    PROJECT = "PROJECT"
    CERTIFICATION = "CERTIFICATION"
    INTERNSHIP = "INTERNSHIP"
    EXPERIENCE = "EXPERIENCE"
    ASSESSMENT = "ASSESSMENT"
    COURSEWORK = "COURSEWORK"
    OTHER = "OTHER"

    @classmethod
    def list(cls):
        return [e.value for e in cls]


class VerificationStatus(str, enum.Enum):
    """Verification statuses."""
    SELF_REPORTED = "SELF_REPORTED"
    VERIFIED = "VERIFIED"
    PENDING = "PENDING"

    @classmethod
    def list(cls):
        return [e.value for e in cls]


class SkillEvidence(db.Model):
    """Skill evidence database model."""
    __tablename__ = "skill_evidence"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    student_id = db.Column(db.Integer, db.ForeignKey("student_profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    skill_id = db.Column(db.Integer, db.ForeignKey("skills.id", ondelete="CASCADE"), nullable=False, index=True)

    evidence_type = db.Column(
        db.Enum(EvidenceType, name="evidence_types", native_enum=False, values_callable=lambda x: [e.value for e in x]),
        nullable=False
    )
    evidence_title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    source_url = db.Column(db.String(500), nullable=True)

    # Related entities (nullable - only one should be set based on evidence_type)
    project_id = db.Column(db.Integer, db.ForeignKey("projects.id", ondelete="SET NULL"), nullable=True, index=True)
    certification_id = db.Column(db.Integer, db.ForeignKey("certifications.id", ondelete="SET NULL"), nullable=True, index=True)
    experience_id = db.Column(db.Integer, db.ForeignKey("experiences.id", ondelete="SET NULL"), nullable=True, index=True)
    internship_id = db.Column(db.Integer, db.ForeignKey("internships.id", ondelete="SET NULL"), nullable=True, index=True)

    verification_status = db.Column(
        db.Enum(VerificationStatus, name="verification_statuses", native_enum=False, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        default=VerificationStatus.SELF_REPORTED
    )
    evidence_strength = db.Column(db.Float, nullable=True)  # 0.0 to 1.0

    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    # Relationships
    student = db.relationship("StudentProfile", backref=db.backref("skill_evidence", cascade="all, delete-orphan"))
    skill = db.relationship("Skill", backref=db.backref("evidence", cascade="all, delete-orphan"))
    project = db.relationship("Project", backref=db.backref("skill_evidence", lazy="dynamic"))
    certification = db.relationship("Certification", backref=db.backref("skill_evidence", lazy="dynamic"))
    experience = db.relationship("Experience", backref=db.backref("skill_evidence", lazy="dynamic"))
    internship = db.relationship("Internship", backref=db.backref("skill_evidence", lazy="dynamic"))

    def __init__(self, student_id: int, skill_id: int, evidence_type: str, evidence_title: str, **kwargs):
        self.student_id = student_id
        self.skill_id = skill_id
        if isinstance(evidence_type, str):
            self.evidence_type = EvidenceType(evidence_type.upper())
        else:
            self.evidence_type = evidence_type
        self.evidence_title = evidence_title.strip()
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)

    def to_dict(self) -> dict:
        """Serialize skill evidence to dictionary."""
        evidence_type = self.evidence_type.value if isinstance(self.evidence_type, EvidenceType) else str(self.evidence_type)
        verification_status = self.verification_status.value if isinstance(self.verification_status, VerificationStatus) else str(self.verification_status)
        return {
            "id": self.id,
            "student_id": self.student_id,
            "skill_id": self.skill_id,
            "skill_name": self.skill.name if self.skill else None,
            "evidence_type": evidence_type,
            "evidence_title": self.evidence_title,
            "description": self.description,
            "source_url": self.source_url,
            "project_id": self.project_id,
            "certification_id": self.certification_id,
            "experience_id": self.experience_id,
            "internship_id": self.internship_id,
            "verification_status": verification_status,
            "evidence_strength": self.evidence_strength,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def __repr__(self) -> str:
        return f"<SkillEvidence {self.id}: {self.evidence_title} for skill {self.skill_id}>"