"""Validated inputs for the industry and student opportunity APIs."""
from marshmallow import Schema, fields, validate
from app.models.opportunity import APPLICATION_STATUSES


class TrimmedString(fields.String):
    def _deserialize(self, value, attr, data, **kwargs):
        return super()._deserialize(value, attr, data, **kwargs).strip()


class CompanyInput(Schema):
    name = TrimmedString(required=True, validate=validate.Length(min=2, max=200))
    website = TrimmedString(allow_none=True, validate=validate.Length(max=500))
    description = TrimmedString(allow_none=True)
    location = TrimmedString(allow_none=True, validate=validate.Length(max=200))


class RequirementInput(Schema):
    skill_id = fields.Integer(required=True, strict=True, validate=validate.Range(min=1))
    required_proficiency = fields.Float(required=True, allow_nan=False, validate=validate.Range(min=0, max=100))
    weight = fields.Float(required=True, allow_nan=False, validate=validate.Range(min=0.001, max=100))


class PostInput(Schema):
    title = TrimmedString(required=True, validate=validate.Length(min=2, max=200))
    description = TrimmedString(required=True, validate=validate.Length(min=5))
    kind = fields.String(required=True, validate=validate.OneOf(['JOB', 'INTERNSHIP']))
    location = TrimmedString(allow_none=True, validate=validate.Length(max=200))
    employment_type = TrimmedString(allow_none=True, validate=validate.Length(max=40))
    eligibility = TrimmedString(allow_none=True)
    deadline = fields.Date(allow_none=True)
    stipend = TrimmedString(allow_none=True, validate=validate.Length(max=100))
    duration = TrimmedString(allow_none=True, validate=validate.Length(max=100))
    required_skills = fields.List(fields.Nested(RequirementInput), required=True, validate=validate.Length(min=1))


class ApplicationStatusInput(Schema):
    status = fields.String(required=True, validate=validate.OneOf(APPLICATION_STATUSES))
