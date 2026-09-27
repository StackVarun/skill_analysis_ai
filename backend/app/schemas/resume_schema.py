"""Validation schemas for resumes."""
from marshmallow import Schema, fields, validate


class ResumeResponseSchema(Schema):
    """Schema for resume response serialization."""
    id = fields.Int(dump_only=True)
    student_id = fields.Int(dump_only=True)
    filename = fields.Str(dump_only=True)
    file_type = fields.Str(dump_only=True)
    file_size = fields.Int(dump_only=True)
    extracted_text_length = fields.Int(dump_only=True)
    status = fields.Str(dump_only=True)
    error_message = fields.Str(dump_only=True)
    created_at = fields.Str(dump_only=True)
    updated_at = fields.Str(dump_only=True)


# Schema instances
resume_response_schema = ResumeResponseSchema()