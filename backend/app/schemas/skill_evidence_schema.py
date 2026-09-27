"""Validation schemas for skill evidence."""
from marshmallow import Schema, fields, validate, validates, ValidationError
from app.models.skill_evidence import EvidenceType, VerificationStatus


class SkillEvidenceSchema(Schema):
    """Schema for skill evidence validation."""
    skill_id = fields.Int(required=True)
    evidence_type = fields.Str(required=True, validate=validate.OneOf(EvidenceType.list()))
    evidence_title = fields.Str(required=True, validate=validate.Length(min=1, max=200))
    description = fields.Str(required=False, allow_none=True)
    source_url = fields.Url(required=False, allow_none=True, validate=validate.Length(max=500))
    project_id = fields.Int(required=False, allow_none=True)
    certification_id = fields.Int(required=False, allow_none=True)
    experience_id = fields.Int(required=False, allow_none=True)
    internship_id = fields.Int(required=False, allow_none=True)
    verification_status = fields.Str(required=False, load_default="SELF_REPORTED", validate=validate.OneOf(VerificationStatus.list()))
    evidence_strength = fields.Float(required=False, allow_none=True, validate=validate.Range(min=0.0, max=1.0))

    @validates("skill_id")
    def validate_skill_id(self, value, **kwargs):
        if not value:
            raise ValidationError("Skill ID is required")

    @validates("evidence_title")
    def validate_evidence_title(self, value, **kwargs):
        if not value or not value.strip():
            raise ValidationError("Evidence title is required")


class SkillEvidenceUpdateSchema(Schema):
    """Schema for skill evidence update validation."""
    evidence_type = fields.Str(required=False, validate=validate.OneOf(EvidenceType.list()))
    evidence_title = fields.Str(required=False, validate=validate.Length(min=1, max=200))
    description = fields.Str(required=False, allow_none=True)
    source_url = fields.Url(required=False, allow_none=True, validate=validate.Length(max=500))
    project_id = fields.Int(required=False, allow_none=True)
    certification_id = fields.Int(required=False, allow_none=True)
    experience_id = fields.Int(required=False, allow_none=True)
    internship_id = fields.Int(required=False, allow_none=True)
    verification_status = fields.Str(required=False, validate=validate.OneOf(VerificationStatus.list()))
    evidence_strength = fields.Float(required=False, allow_none=True, validate=validate.Range(min=0.0, max=1.0))


class SkillEvidenceResponseSchema(Schema):
    """Schema for skill evidence response serialization."""
    id = fields.Int(dump_only=True)
    student_id = fields.Int(dump_only=True)
    skill_id = fields.Int(dump_only=True)
    skill_name = fields.Str(dump_only=True)
    evidence_type = fields.Str(dump_only=True)
    evidence_title = fields.Str(dump_only=True)
    description = fields.Str(dump_only=True)
    source_url = fields.Str(dump_only=True)
    project_id = fields.Int(dump_only=True)
    certification_id = fields.Int(dump_only=True)
    experience_id = fields.Int(dump_only=True)
    internship_id = fields.Int(dump_only=True)
    verification_status = fields.Str(dump_only=True)
    evidence_strength = fields.Float(dump_only=True)
    created_at = fields.Str(dump_only=True)
    updated_at = fields.Str(dump_only=True)


# Schema instances
skill_evidence_schema = SkillEvidenceSchema()
skill_evidence_update_schema = SkillEvidenceUpdateSchema()
skill_evidence_response_schema = SkillEvidenceResponseSchema()