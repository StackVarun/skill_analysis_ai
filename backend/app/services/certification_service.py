"""Certification service for business logic."""
from app.extensions import db
from app.models.student_profile import StudentProfile
from app.models.certification import Certification


class CertificationService:
    """Service layer for certification operations."""

    @staticmethod
    def get_student_certifications(student_id: int):
        """Get all certifications for a student."""
        return Certification.query.filter_by(student_id=student_id).order_by(Certification.issue_date.desc()).all()

    @staticmethod
    def get_certification_by_id(cert_id: int):
        """Get certification by ID."""
        return Certification.query.filter_by(id=cert_id).first()

    @staticmethod
    def get_student_certification(student_id: int, cert_id: int):
        """Get a specific student's certification."""
        return Certification.query.filter_by(student_id=student_id, id=cert_id).first()

    @staticmethod
    def create_certification(student_id: int, name: str, issuing_organization: str, issue_date,
                             expiry_date=None, credential_id=None, credential_url=None, description=None) -> Certification:
        """Create a new certification for a student."""
        student = StudentProfile.query.filter_by(id=student_id).first()
        if not student:
            raise ValueError("Student profile not found")

        cert = Certification(
            student_id=student_id,
            name=name,
            issuing_organization=issuing_organization,
            issue_date=issue_date,
            expiry_date=expiry_date,
            credential_id=credential_id,
            credential_url=credential_url,
            description=description
        )

        db.session.add(cert)
        db.session.commit()
        return cert

    @staticmethod
    def update_certification(cert_id: int, student_id: int, data: dict) -> Certification:
        """Update a student's certification."""
        cert = Certification.query.filter_by(id=cert_id, student_id=student_id).first()
        if not cert:
            raise ValueError("Certification not found")

        for key, value in data.items():
            if hasattr(cert, key) and key not in ("id", "student_id", "created_at"):
                setattr(cert, key, value)

        db.session.commit()
        return cert

    @staticmethod
    def delete_certification(cert_id: int, student_id: int) -> bool:
        """Delete a student's certification."""
        cert = Certification.query.filter_by(id=cert_id, student_id=student_id).first()
        if not cert:
            return False
        db.session.delete(cert)
        db.session.commit()
        return True