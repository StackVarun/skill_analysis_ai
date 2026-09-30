"""Validation schemas for projects."""
from marshmallow import Schema, fields, validate, validates, ValidationError


class ProjectSchema(Schema):
    """Schema for project validation."""
    title = fields.Str(required=True, validate=validate.Length(min=1, max=200))
    completion_status = fields.Str(load_default="COMPLETED", validate=validate.OneOf(["IN_PROGRESS", "COMPLETED"]))
    description = fields.Str(required=False, allow_none=True)
    technologies = fields.Str(required=False, allow_none=True)
    project_url = fields.Url(required=False, allow_none=True, validate=validate.Length(max=500))
    github_url = fields.Url(required=False, allow_none=True, validate=validate.Length(max=500))
    start_date = fields.Date(required=False, allow_none=True)
    end_date = fields.Date(required=False, allow_none=True)
    role = fields.Str(required=False, allow_none=True, validate=validate.Length(max=200))
    skill_ids = fields.List(fields.Int(), required=False, load_default=[])

    @validates("title")
    def validate_title(self, value, **kwargs):
        if not value or not value.strip():
            raise ValidationError("Project title is required")


class ProjectUpdateSchema(Schema):
    """Schema for project update validation."""
    title = fields.Str(required=False, validate=validate.Length(min=1, max=200))
    completion_status = fields.Str(validate=validate.OneOf(["IN_PROGRESS", "COMPLETED"]))

    @validates("title")
    def validate_title(self, value, **kwargs):
        if not value.strip():
            raise ValidationError("Project title is required")
    description = fields.Str(required=False, allow_none=True)
    technologies = fields.Str(required=False, allow_none=True)
    project_url = fields.Url(required=False, allow_none=True, validate=validate.Length(max=500))
    github_url = fields.Url(required=False, allow_none=True, validate=validate.Length(max=500))
    start_date = fields.Date(required=False, allow_none=True)
    end_date = fields.Date(required=False, allow_none=True)
    role = fields.Str(required=False, allow_none=True, validate=validate.Length(max=200))
    skill_ids = fields.List(fields.Int(), required=False)


class ProjectResponseSchema(Schema):
    """Schema for project response serialization."""
    id = fields.Int(dump_only=True)
    completion_status = fields.Str(dump_only=True)
    verification_status = fields.Str(dump_only=True)
    student_id = fields.Int(dump_only=True)
    title = fields.Str(dump_only=True)
    description = fields.Str(dump_only=True)
    technologies = fields.Str(dump_only=True)
    project_url = fields.Str(dump_only=True)
    github_url = fields.Str(dump_only=True)
    start_date = fields.Str(dump_only=True)
    end_date = fields.Str(dump_only=True)
    role = fields.Str(dump_only=True)
    skills = fields.List(fields.Dict(), dump_only=True)
    created_at = fields.Str(dump_only=True)
    updated_at = fields.Str(dump_only=True)


# Schema instances
project_schema = ProjectSchema()
project_update_schema = ProjectUpdateSchema()
project_response_schema = ProjectResponseSchema()