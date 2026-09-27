"""Certification model."""
from datetime import datetime, timezone
from app.extensions import db
from app.models.student_profile import StudentProfile


class Certification(db.Model):
    """Certification database model."""
    __tablename__ = "certifications"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    student_id = db.Column(db.Integer, db.ForeignKey("student_profiles.id", ondelete="CASCADE"), nullable=False, index=True)

    name = db.Column(db.String(200), nullable=False)
    issuing_organization = db.Column(db.String(200), nullable=False)
    issue_date = db.Column(db.Date, nullable=False)
    expiry_date = db.Column(db.Date, nullable=True)
    credential_id = db.Column(db.String(100), nullable=True)
    credential_url = db.Column(db.String(500), nullable=True)
    description = db.Column(db.Text, nullable=True)

    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    student = db.relationship("StudentProfile", backref=db.backref("certifications", cascade="all, delete-orphan"))

    def __init__(self, student_id: int, name: str, issuing_organization: str, issue_date, **kwargs):
        self.student_id = student_id
        self.name = name.strip()
        self.issuing_organization = issuing_organization.strip()
        self.issue_date = issue_date
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)

    def to_dict(self) -> dict:
        """Serialize certification to dictionary."""
        return {
            "id": self.id,
            "student_id": self.student_id,
            "name": self.name,
            "issuing_organization": self.issuing_organization,
            "issue_date": self.issue_date.isoformat() if self.issue_date else None,
            "expiry_date": self.expiry_date.isoformat() if self.expiry_date else None,
            "credential_id": self.credential_id,
            "credential_url": self.credential_url,
            "description": self.description,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def __repr__(self) -> str:
        return f"<Certification {self.id}: {self.name}>"