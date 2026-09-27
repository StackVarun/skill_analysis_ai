"""Validation schemas for student profile."""
from marshmallow import Schema, fields, validate, validates, ValidationError


class StudentProfileSchema(Schema):
    """Schema for student profile validation."""
    full_name = fields.Str(required=False, allow_none=True, validate=validate.Length(max=200))
    phone = fields.Str(required=False, allow_none=True, validate=validate.Length(max=30))
    institution = fields.Str(required=False, allow_none=True, validate=validate.Length(max=200))
    degree = fields.Str(required=False, allow_none=True, validate=validate.Length(max=200))
    branch = fields.Str(required=False, allow_none=True, validate=validate.Length(max=200))
    graduation_year = fields.Int(required=False, allow_none=True, validate=validate.Range(min=1900, max=2100))
    cgpa = fields.Float(required=False, allow_none=True, validate=validate.Range(min=0.0, max=10.0))
    bio = fields.Str(required=False, allow_none=True)
    location = fields.Str(required=False, allow_none=True, validate=validate.Length(max=200))
    linkedin_url = fields.Url(required=False, allow_none=True, validate=validate.Length(max=500))
    github_url = fields.Url(required=False, allow_none=True, validate=validate.Length(max=500))
    portfolio_url = fields.Url(required=False, allow_none=True, validate=validate.Length(max=500))

    @validates("phone")
    def validate_phone(self, value, **kwargs):
        if value and not value.strip():
            raise ValidationError("Phone cannot be empty string")

    @validates("linkedin_url")
    def validate_linkedin_url(self, value, **kwargs):
        if value and "linkedin.com" not in value:
            raise ValidationError("LinkedIn URL must be a valid linkedin.com URL")

    @validates("github_url")
    def validate_github_url(self, value, **kwargs):
        if value and "github.com" not in value:
            raise ValidationError("GitHub URL must be a valid github.com URL")


class StudentProfileResponseSchema(Schema):
    """Schema for student profile response serialization."""
    id = fields.Int(dump_only=True)
    user_id = fields.Int(dump_only=True)
    full_name = fields.Str(dump_only=True)
    phone = fields.Str(dump_only=True)
    institution = fields.Str(dump_only=True)
    degree = fields.Str(dump_only=True)
    branch = fields.Str(dump_only=True)
    graduation_year = fields.Int(dump_only=True)
    cgpa = fields.Float(dump_only=True)
    bio = fields.Str(dump_only=True)
    location = fields.Str(dump_only=True)
    linkedin_url = fields.Str(dump_only=True)
    github_url = fields.Str(dump_only=True)
    portfolio_url = fields.Str(dump_only=True)
    created_at = fields.Str(dump_only=True)
    updated_at = fields.Str(dump_only=True)


# Schema instances
student_profile_schema = StudentProfileSchema()
student_profile_response_schema = StudentProfileResponseSchema()