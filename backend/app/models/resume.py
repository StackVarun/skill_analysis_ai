"""Resume model."""
import enum
import os
import uuid
from datetime import datetime, timezone
from app.extensions import db
from app.models.student_profile import StudentProfile


class ResumeStatus(str, enum.Enum):
    """Resume processing status."""
    UPLOADED = "UPLOADED"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"

    @classmethod
    def list(cls):
        return [e.value for e in cls]


class Resume(db.Model):
    """Resume database model."""
    __tablename__ = "resumes"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    student_id = db.Column(db.Integer, db.ForeignKey("student_profiles.id", ondelete="CASCADE"), nullable=False, index=True)

    filename = db.Column(db.String(255), nullable=False)
    file_type = db.Column(db.String(20), nullable=False)  # pdf, docx
    file_size = db.Column(db.Integer, nullable=True)
    file_path = db.Column(db.String(500), nullable=False)

    extracted_text = db.Column(db.Text, nullable=True)
    extracted_text_length = db.Column(db.Integer, nullable=True)

    status = db.Column(
        db.Enum(ResumeStatus, name="resume_statuses", native_enum=False, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        default=ResumeStatus.UPLOADED
    )
    error_message = db.Column(db.Text, nullable=True)

    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    student = db.relationship("StudentProfile", backref=db.backref("resumes", cascade="all, delete-orphan"))

    def __init__(self, student_id: int, filename: str, file_type: str, file_path: str, file_size: int = None, status=None):
        self.student_id = student_id
        self.filename = filename
        self.file_type = file_type.lower()
        self.file_path = file_path
        self.file_size = file_size
        if status:
            self.status = status

    def to_dict(self) -> dict:
        """Serialize resume to dictionary."""
        status_val = self.status.value if isinstance(self.status, ResumeStatus) else str(self.status)
        return {
            "id": self.id,
            "student_id": self.student_id,
            "filename": self.filename,
            "file_type": self.file_type,
            "file_size": self.file_size,
            "extracted_text_length": self.extracted_text_length,
            "status": status_val,
            "error_message": self.error_message,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def __repr__(self) -> str:
        return f"<Resume {self.id}: {self.filename}>"


# Upload configuration
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "uploads", "resumes")
ALLOWED_EXTENSIONS = {"pdf", "docx"}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB