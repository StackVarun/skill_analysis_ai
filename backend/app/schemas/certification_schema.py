"""Validation schemas for certifications."""
from marshmallow import Schema, fields, validate, validates, ValidationError


class CertificationSchema(Schema):
    """Schema for certification validation."""
    name = fields.Str(required=True, validate=validate.Length(min=1, max=200))
    issuing_organization = fields.Str(required=True, validate=validate.Length(min=1, max=200))
    issue_date = fields.Date(required=True)
    expiry_date = fields.Date(required=False, allow_none=True)
    credential_id = fields.Str(required=False, allow_none=True, validate=validate.Length(max=100))
    credential_url = fields.Url(required=False, allow_none=True, validate=validate.Length(max=500))
    description = fields.Str(required=False, allow_none=True)

    @validates("name")
    def validate_name(self, value, **kwargs):
        if not value or not value.strip():
            raise ValidationError("Certification name is required")

    @validates("issuing_organization")
    def validate_issuing_organization(self, value, **kwargs):
        if not value or not value.strip():
            raise ValidationError("Issuing organization is required")


class CertificationUpdateSchema(Schema):
    """Schema for certification update validation."""
    name = fields.Str(required=False, validate=validate.Length(min=1, max=200))
    issuing_organization = fields.Str(required=False, validate=validate.Length(min=1, max=200))
    issue_date = fields.Date(required=False)
    expiry_date = fields.Date(required=False, allow_none=True)
    credential_id = fields.Str(required=False, allow_none=True, validate=validate.Length(max=100))
    credential_url = fields.Url(required=False, allow_none=True, validate=validate.Length(max=500))
    description = fields.Str(required=False, allow_none=True)


class CertificationResponseSchema(Schema):
    """Schema for certification response serialization."""
    id = fields.Int(dump_only=True)
    student_id = fields.Int(dump_only=True)
    name = fields.Str(dump_only=True)
    issuing_organization = fields.Str(dump_only=True)
    issue_date = fields.Str(dump_only=True)
    expiry_date = fields.Str(dump_only=True)
    credential_id = fields.Str(dump_only=True)
    credential_url = fields.Str(dump_only=True)
    description = fields.Str(dump_only=True)
    created_at = fields.Str(dump_only=True)
    updated_at = fields.Str(dump_only=True)


# Schema instances
certification_schema = CertificationSchema()
certification_update_schema = CertificationUpdateSchema()
certification_response_schema = CertificationResponseSchema()