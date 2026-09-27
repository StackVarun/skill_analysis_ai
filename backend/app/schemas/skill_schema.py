"""Validation schemas for skills."""
from marshmallow import Schema, fields, validate, validates, ValidationError


class SkillSchema(Schema):
    """Schema for skill validation."""
    name = fields.Str(required=True, validate=validate.Length(min=1, max=100))
    category = fields.Str(required=False, allow_none=True, validate=validate.Length(max=100))
    description = fields.Str(required=False, allow_none=True)

    @validates("name")
    def validate_name(self, value, **kwargs):
        if not value or not value.strip():
            raise ValidationError("Skill name is required")


class SkillResponseSchema(Schema):
    """Schema for skill response serialization."""
    id = fields.Int(dump_only=True)
    name = fields.Str(dump_only=True)
    category = fields.Str(dump_only=True)
    description = fields.Str(dump_only=True)
    created_at = fields.Str(dump_only=True)
    updated_at = fields.Str(dump_only=True)


# Schema instances
skill_schema = SkillSchema()
skill_response_schema = SkillResponseSchema()