"""Validation schemas for Phase 3 endpoints."""
from marshmallow import Schema, fields, validate, validates_schema, ValidationError


class QuestionInputSchema(Schema):
    skill_id = fields.Integer(required=True, validate=validate.Range(min=1))
    prompt = fields.String(required=True, validate=validate.Length(min=1, max=3000))
    options = fields.List(fields.String(validate=validate.Length(min=1, max=500)), required=True, validate=validate.Length(min=2, max=20))
    correct_answer = fields.String(required=True, validate=validate.Length(min=1, max=500))

    @validates_schema
    def validate_answer(self, data, **kwargs):
        if data.get("correct_answer") not in data.get("options", []):
            raise ValidationError({"correct_answer": ["Must be one of the options."]})


class AssessmentInputSchema(Schema):
    title = fields.String(required=True, validate=validate.Length(min=1, max=200))
    description = fields.String(load_default=None, allow_none=True)
    skill_id = fields.Integer(required=True, validate=validate.Range(min=1))
    questions = fields.List(fields.Nested(QuestionInputSchema), required=True, validate=validate.Length(min=1))


class AnswerInputSchema(Schema):
    question_id = fields.Integer(required=True, validate=validate.Range(min=1))
    answer = fields.String(required=True, validate=validate.Length(min=1, max=500))


class SubmissionSchema(Schema):
    answers = fields.List(fields.Nested(AnswerInputSchema), required=True, validate=validate.Length(min=1))


class RequirementInputSchema(Schema):
    skill_id = fields.Integer(required=True, validate=validate.Range(min=1))
    required_proficiency = fields.Float(required=True, validate=validate.Range(min=0, max=100))
    weight = fields.Float(load_default=1.0, validate=validate.Range(min=0.0001))


class RoleInputSchema(Schema):
    name = fields.String(required=True, validate=validate.Length(min=1, max=120))
    description = fields.String(load_default=None, allow_none=True)
    requirements = fields.List(fields.Nested(RequirementInputSchema), required=True, validate=validate.Length(min=1))

    @validates_schema
    def unique_skills(self, data, **kwargs):
        ids = [r["skill_id"] for r in data.get("requirements", [])]
        if len(ids) != len(set(ids)):
            raise ValidationError({"requirements": ["Skill requirements must be unique."]})
