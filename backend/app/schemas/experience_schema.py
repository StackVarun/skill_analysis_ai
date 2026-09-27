"""Validation schemas for experiences."""
from marshmallow import Schema, fields, validate, validates, ValidationError
from app.models.experience import EmploymentType


class ExperienceSchema(Schema):
    """Schema for experience validation."""
    organization = fields.Str(required=True, validate=validate.Length(min=1, max=200))
    job_title = fields.Str(required=True, validate=validate.Length(min=1, max=200))
    employment_type = fields.Str(required=False, load_default="FULL_TIME", validate=validate.OneOf(EmploymentType.list()))
    location = fields.Str(required=False, allow_none=True, validate=validate.Length(max=200))
    start_date = fields.Date(required=True)
    end_date = fields.Date(required=False, allow_none=True)
    description = fields.Str(required=False, allow_none=True)
    skill_ids = fields.List(fields.Int(), required=False, load_default=[])

    @validates("organization")
    def validate_organization(self, value, **kwargs):
        if not value or not value.strip():
            raise ValidationError("Organization is required")

    @validates("job_title")
    def validate_job_title(self, value, **kwargs):
        if not value or not value.strip():
            raise ValidationError("Job title is required")


class ExperienceUpdateSchema(Schema):
    """Schema for experience update validation."""
    organization = fields.Str(required=False, validate=validate.Length(min=1, max=200))
    job_title = fields.Str(required=False, validate=validate.Length(min=1, max=200))
    employment_type = fields.Str(required=False, validate=validate.OneOf(EmploymentType.list()))
    location = fields.Str(required=False, allow_none=True, validate=validate.Length(max=200))
    start_date = fields.Date(required=False)
    end_date = fields.Date(required=False, allow_none=True)
    description = fields.Str(required=False, allow_none=True)
    skill_ids = fields.List(fields.Int(), required=False)


class ExperienceResponseSchema(Schema):
    """Schema for experience response serialization."""
    id = fields.Int(dump_only=True)
    student_id = fields.Int(dump_only=True)
    organization = fields.Str(dump_only=True)
    job_title = fields.Str(dump_only=True)
    employment_type = fields.Str(dump_only=True)
    location = fields.Str(dump_only=True)
    start_date = fields.Str(dump_only=True)
    end_date = fields.Str(dump_only=True)
    description = fields.Str(dump_only=True)
    skills = fields.List(fields.Dict(), dump_only=True)
    created_at = fields.Str(dump_only=True)
    updated_at = fields.Str(dump_only=True)


# Schema instances
experience_schema = ExperienceSchema()
experience_update_schema = ExperienceUpdateSchema()
experience_response_schema = ExperienceResponseSchema()