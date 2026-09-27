"""Validation schemas for student skills."""
from marshmallow import Schema, fields, validate, validates, ValidationError
from app.models.student_skill import ProficiencyLevel


class StudentSkillSchema(Schema):
    """Schema for student skill validation."""
    skill_id = fields.Int(required=True)
    proficiency = fields.Str(required=False, load_default="BEGINNER", validate=validate.OneOf(ProficiencyLevel.list()))
    years_experience = fields.Int(required=False, allow_none=True, validate=validate.Range(min=0, max=50))
    months_experience = fields.Int(required=False, allow_none=True, validate=validate.Range(min=0, max=11))
    source = fields.Str(required=False, allow_none=True, validate=validate.Length(max=200))

    @validates("skill_id")
    def validate_skill_id(self, value, **kwargs):
        if not value:
            raise ValidationError("Skill ID is required")


class StudentSkillUpdateSchema(Schema):
    """Schema for student skill update validation."""
    proficiency = fields.Str(required=False, validate=validate.OneOf(ProficiencyLevel.list()))
    years_experience = fields.Int(required=False, allow_none=True, validate=validate.Range(min=0, max=50))
    months_experience = fields.Int(required=False, allow_none=True, validate=validate.Range(min=0, max=11))
    source = fields.Str(required=False, allow_none=True, validate=validate.Length(max=200))


class StudentSkillResponseSchema(Schema):
    """Schema for student skill response serialization."""
    id = fields.Int(dump_only=True)
    student_id = fields.Int(dump_only=True)
    skill_id = fields.Int(dump_only=True)
    skill_name = fields.Str(dump_only=True)
    skill_category = fields.Str(dump_only=True)
    proficiency = fields.Str(dump_only=True)
    years_experience = fields.Int(dump_only=True)
    months_experience = fields.Int(dump_only=True)
    source = fields.Str(dump_only=True)
    created_at = fields.Str(dump_only=True)
    updated_at = fields.Str(dump_only=True)


# Schema instances
student_skill_schema = StudentSkillSchema()
student_skill_update_schema = StudentSkillUpdateSchema()
student_skill_response_schema = StudentSkillResponseSchema()