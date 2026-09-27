"""Project model."""
from datetime import datetime, timezone
from app.extensions import db
from app.models.student_profile import StudentProfile
from app.models.skill import Skill


class Project(db.Model):
    """Project database model."""
    __tablename__ = "projects"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    student_id = db.Column(db.Integer, db.ForeignKey("student_profiles.id", ondelete="CASCADE"), nullable=False, index=True)

    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    technologies = db.Column(db.Text, nullable=True)  # Comma-separated or JSON
    project_url = db.Column(db.String(500), nullable=True)
    github_url = db.Column(db.String(500), nullable=True)
    start_date = db.Column(db.Date, nullable=True)
    end_date = db.Column(db.Date, nullable=True)
    role = db.Column(db.String(200), nullable=True)

    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    # Relationships
    student = db.relationship("StudentProfile", backref=db.backref("projects", cascade="all, delete-orphan"))
    skills = db.relationship("Skill", secondary="project_skills", backref=db.backref("projects", lazy="dynamic"))

    def __init__(self, student_id: int, title: str, **kwargs):
        self.student_id = student_id
        self.title = title.strip()
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)

    def to_dict(self) -> dict:
        """Serialize project to dictionary."""
        return {
            "id": self.id,
            "student_id": self.student_id,
            "title": self.title,
            "description": self.description,
            "technologies": self.technologies,
            "project_url": self.project_url,
            "github_url": self.github_url,
            "start_date": self.start_date.isoformat() if self.start_date else None,
            "end_date": self.end_date.isoformat() if self.end_date else None,
            "role": self.role,
            "skills": [{"id": s.id, "name": s.name, "category": s.category} for s in self.skills],
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def __repr__(self) -> str:
        return f"<Project {self.id}: {self.title}>"


# Association table for project-skills many-to-many relationship
project_skills = db.Table(
    "project_skills",
    db.Column("project_id", db.Integer, db.ForeignKey("projects.id", ondelete="CASCADE"), primary_key=True),
    db.Column("skill_id", db.Integer, db.ForeignKey("skills.id", ondelete="CASCADE"), primary_key=True)
)