"""Skill evidence service for business logic."""
from app.extensions import db
from app.models.student_profile import StudentProfile
from app.models.skill import Skill
from app.models.skill_evidence import SkillEvidence, EvidenceType, VerificationStatus
from app.models.project import Project
from app.models.certification import Certification
from app.models.experience import Experience
from app.models.internship import Internship


class SkillEvidenceService:
    """Service layer for skill evidence operations."""

    @staticmethod
    def get_student_evidence(student_id: int):
        """Get all skill evidence for a student."""
        return SkillEvidence.query.filter_by(student_id=student_id).order_by(SkillEvidence.created_at.desc()).all()

    @staticmethod
    def get_evidence_by_id(evidence_id: int):
        """Get skill evidence by ID."""
        return SkillEvidence.query.filter_by(id=evidence_id).first()

    @staticmethod
    def get_student_evidence_by_id(student_id: int, evidence_id: int):
        """Get a specific student's skill evidence."""
        return SkillEvidence.query.filter_by(student_id=student_id, id=evidence_id).first()

    @staticmethod
    def get_evidence_for_skill(student_id: int, skill_id: int):
        """Get all evidence for a specific skill of a student."""
        return SkillEvidence.query.filter_by(student_id=student_id, skill_id=skill_id).all()

    @staticmethod
    def create_evidence(student_id: int, skill_id: int, evidence_type: str, evidence_title: str,
                        description=None, source_url=None, project_id=None, certification_id=None,
                        experience_id=None, internship_id=None, verification_status="SELF_REPORTED",
                        evidence_strength=None) -> SkillEvidence:
        """Create new skill evidence for a student."""
        student = StudentProfile.query.filter_by(id=student_id).first()
        if not student:
            raise ValueError("Student profile not found")

        skill = Skill.query.filter_by(id=skill_id).first()
        if not skill:
            raise ValueError("Skill not found")

        try:
            ev_type = EvidenceType(evidence_type.upper())
        except ValueError:
            raise ValueError(f"Invalid evidence type. Must be one of: {', '.join(EvidenceType.list())}")

        try:
            ver_status = VerificationStatus(verification_status.upper())
        except ValueError:
            raise ValueError(f"Invalid verification status. Must be one of: {', '.join(VerificationStatus.list())}")

        # Validate related entity exists if provided
        if project_id:
            project = Project.query.filter_by(id=project_id, student_id=student_id).first()
            if not project:
                raise ValueError("Project not found or not owned by student")

        if certification_id:
            cert = Certification.query.filter_by(id=certification_id, student_id=student_id).first()
            if not cert:
                raise ValueError("Certification not found or not owned by student")

        if experience_id:
            exp = Experience.query.filter_by(id=experience_id, student_id=student_id).first()
            if not exp:
                raise ValueError("Experience not found or not owned by student")

        if internship_id:
            intern = Internship.query.filter_by(id=internship_id, student_id=student_id).first()
            if not intern:
                raise ValueError("Internship not found or not owned by student")

        evidence = SkillEvidence(
            student_id=student_id,
            skill_id=skill_id,
            evidence_type=ev_type,
            evidence_title=evidence_title,
            description=description,
            source_url=source_url,
            project_id=project_id,
            certification_id=certification_id,
            experience_id=experience_id,
            internship_id=internship_id,
            verification_status=ver_status,
            evidence_strength=evidence_strength
        )

        db.session.add(evidence)
        db.session.flush()
        from app.services.faculty_support_service import queue_review
        queue_review(student_id, "EVIDENCE", evidence.id)
        db.session.commit()
        return evidence

    @staticmethod
    def update_evidence(evidence_id: int, student_id: int, data: dict) -> SkillEvidence:
        """Update a student's skill evidence."""
        evidence = SkillEvidence.query.filter_by(id=evidence_id, student_id=student_id).first()
        if not evidence:
            raise ValueError("Skill evidence not found")

        if "evidence_type" in data and data["evidence_type"]:
            try:
                evidence.evidence_type = EvidenceType(data["evidence_type"].upper())
            except ValueError:
                raise ValueError(f"Invalid evidence type. Must be one of: {', '.join(EvidenceType.list())}")

        if "verification_status" in data and data["verification_status"]:
            try:
                evidence.verification_status = VerificationStatus(data["verification_status"].upper())
            except ValueError:
                raise ValueError(f"Invalid verification status. Must be one of: {', '.join(VerificationStatus.list())}")

        # Validate related entities if provided
        if "project_id" in data and data["project_id"]:
            project = Project.query.filter_by(id=data["project_id"], student_id=student_id).first()
            if not project:
                raise ValueError("Project not found or not owned by student")

        if "certification_id" in data and data["certification_id"]:
            cert = Certification.query.filter_by(id=data["certification_id"], student_id=student_id).first()
            if not cert:
                raise ValueError("Certification not found or not owned by student")

        if "experience_id" in data and data["experience_id"]:
            exp = Experience.query.filter_by(id=data["experience_id"], student_id=student_id).first()
            if not exp:
                raise ValueError("Experience not found or not owned by student")

        if "internship_id" in data and data["internship_id"]:
            intern = Internship.query.filter_by(id=data["internship_id"], student_id=student_id).first()
            if not intern:
                raise ValueError("Internship not found or not owned by student")

        before = evidence.to_dict()
        for key, value in data.items():
            if hasattr(evidence, key) and key not in ("id", "student_id", "skill_id", "created_at"):
                setattr(evidence, key, value)

        after = evidence.to_dict()
        if any(before[k] != after[k] for k in ("evidence_type", "evidence_title", "description", "source_url", "project_id", "certification_id", "experience_id", "internship_id", "evidence_strength", "verification_status")):
            evidence.verification_status = VerificationStatus.SELF_REPORTED
            from app.services.faculty_support_service import queue_review
            queue_review(student_id, "EVIDENCE", evidence.id, reset=True)
            if evidence.project and evidence.project.verification_request:
                queue_review(student_id, "PROJECT", evidence.project_id, reset=True)
        db.session.commit()
        return evidence

    @staticmethod
    def delete_evidence(evidence_id: int, student_id: int) -> bool:
        """Delete a student's skill evidence."""
        evidence = SkillEvidence.query.filter_by(id=evidence_id, student_id=student_id).first()
        if not evidence:
            return False
        db.session.delete(evidence)
        db.session.commit()
        return True