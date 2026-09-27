"""Student profile model."""
from datetime import datetime, timezone
from app.extensions import db
from app.models.user import User


class StudentProfile(db.Model):
    """Student profile database model."""
    __tablename__ = "student_profiles"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)

    full_name = db.Column(db.String(200), nullable=True)
    phone = db.Column(db.String(30), nullable=True)
    institution = db.Column(db.String(200), nullable=True)
    degree = db.Column(db.String(200), nullable=True)
    branch = db.Column(db.String(200), nullable=True)
    graduation_year = db.Column(db.Integer, nullable=True)
    cgpa = db.Column(db.Float, nullable=True)
    bio = db.Column(db.Text, nullable=True)
    location = db.Column(db.String(200), nullable=True)
    linkedin_url = db.Column(db.String(500), nullable=True)
    github_url = db.Column(db.String(500), nullable=True)
    portfolio_url = db.Column(db.String(500), nullable=True)

    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    user = db.relationship("User", backref=db.backref("student_profile", uselist=False, cascade="all, delete-orphan"))

    def __init__(self, user_id, **kwargs):
        self.user_id = user_id
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)

    def to_dict(self) -> dict:
        """Serialize profile to dictionary."""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "full_name": self.full_name,
            "phone": self.phone,
            "institution": self.institution,
            "degree": self.degree,
            "branch": self.branch,
            "graduation_year": self.graduation_year,
            "cgpa": self.cgpa,
            "bio": self.bio,
            "location": self.location,
            "linkedin_url": self.linkedin_url,
            "github_url": self.github_url,
            "portfolio_url": self.portfolio_url,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def __repr__(self) -> str:
        return f"<StudentProfile {self.id}: user_id={self.user_id}>"