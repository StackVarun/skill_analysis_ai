"""Input validation for the optional local AI API."""
from marshmallow import Schema, fields, validate


class ResumeExtractionInputSchema(Schema):
    resume_id = fields.Integer(required=True, validate=validate.Range(min=1))


class SkillNormalizationInputSchema(Schema):
    variant = fields.String(required=True, validate=validate.Length(min=1, max=100))


class GapExplanationInputSchema(Schema):
    role_id = fields.Integer(required=True, validate=validate.Range(min=1))


class RoadmapInputSchema(Schema):
    role_id = fields.Integer(required=True, validate=validate.Range(min=1))
