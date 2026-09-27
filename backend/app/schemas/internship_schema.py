"""Validation schemas for internships."""
from marshmallow import Schema, fields, validate, validates, ValidationError
from app.models.internship import InternshipType, InternshipStatus


class InternshipSchema(Schema):
    """Schema for internship validation."""
    organization = fields.Str(required=True, validate=validate.Length(min=1, max=200))
    role = fields.Str(required=True, validate=validate.Length(min=1, max=200))
    start_date = fields.Date(required=True)
    end_date = fields.Date(required=False, allow_none=True)
    description = fields.Str(required=False, allow_none=True)
    certificate_url = fields.Url(required=False, allow_none=True, validate=validate.Length(max=500))
    internship_type = fields.Str(required=False, load_default="SUMMER", validate=validate.OneOf(InternshipType.list()))
    status = fields.Str(required=False, load_default="COMPLETED", validate=validate.OneOf(InternshipStatus.list()))
    skill_ids = fields.List(fields.Int(), required=False, load_default=[])

    @validates("organization")
    def validate_organization(self, value, **kwargs):
        if not value or not value.strip():
            raise ValidationError("Organization is required")

    @validates("role")
    def validate_role(self, value, **kwargs):
        if not value or not value.strip():
            raise ValidationError("Role is required")


class InternshipUpdateSchema(Schema):
    """Schema for internship update validation."""
    organization = fields.Str(required=False, validate=validate.Length(min=1, max=200))
    role = fields.Str(required=False, validate=validate.Length(min=1, max=200))
    start_date = fields.Date(required=False)
    end_date = fields.Date(required=False, allow_none=True)
    description = fields.Str(required=False, allow_none=True)
    certificate_url = fields.Url(required=False, allow_none=True, validate=validate.Length(max=500))
    internship_type = fields.Str(required=False, validate=validate.OneOf(InternshipType.list()))
    status = fields.Str(required=False, validate=validate.OneOf(InternshipStatus.list()))
    skill_ids = fields.List(fields.Int(), required=False)


class InternshipResponseSchema(Schema):
    """Schema for internship response serialization."""
    id = fields.Int(dump_only=True)
    student_id = fields.Int(dump_only=True)
    organization = fields.Str(dump_only=True)
    role = fields.Str(dump_only=True)
    start_date = fields.Str(dump_only=True)
    end_date = fields.Str(dump_only=True)
    description = fields.Str(dump_only=True)
    certificate_url = fields.Str(dump_only=True)
    internship_type = fields.Str(dump_only=True)
    status = fields.Str(dump_only=True)
    skills = fields.List(fields.Dict(), dump_only=True)
    created_at = fields.Str(dump_only=True)
    updated_at = fields.Str(dump_only=True)


# Schema instances
internship_schema = InternshipSchema()
internship_update_schema = InternshipUpdateSchema()
internship_response_schema = InternshipResponseSchema()