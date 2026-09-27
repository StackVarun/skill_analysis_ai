"""Validation schemas for authentication."""
from marshmallow import Schema, fields, validate, validates, ValidationError
from app.models.enums import UserRole


class RegisterSchema(Schema):
    """Schema for user registration validation."""
    email = fields.Email(required=True, validate=validate.Length(max=120))
    password = fields.Str(required=True, validate=validate.Length(min=8, max=100))
    first_name = fields.Str(required=True, validate=validate.Length(min=1, max=100))
    last_name = fields.Str(required=True, validate=validate.Length(min=1, max=100))
    role = fields.Str(required=False, load_default="STUDENT", validate=validate.OneOf(UserRole.list()))

    @validates("email")
    def validate_email(self, value, **kwargs):
        if not value or not value.strip():
            raise ValidationError("Email is required")

    @validates("password")
    def validate_password(self, value, **kwargs):
        if not value or not value.strip():
            raise ValidationError("Password is required")


class LoginSchema(Schema):
    """Schema for user login validation."""
    email = fields.Email(required=True)
    password = fields.Str(required=True)

    @validates("email")
    def validate_email(self, value, **kwargs):
        if not value or not value.strip():
            raise ValidationError("Email is required")

    @validates("password")
    def validate_password(self, value, **kwargs):
        if not value:
            raise ValidationError("Password is required")


class UserResponseSchema(Schema):
    """Schema for user response serialization."""
    id = fields.Int(dump_only=True)
    email = fields.Email(dump_only=True)
    first_name = fields.Str(dump_only=True)
    last_name = fields.Str(dump_only=True)
    full_name = fields.Str(dump_only=True)
    role = fields.Str(dump_only=True)
    is_active = fields.Bool(dump_only=True)
    created_at = fields.Str(dump_only=True)
    updated_at = fields.Str(dump_only=True)


class AuthResponseSchema(Schema):
    """Schema for authentication response."""
    access_token = fields.Str(dump_only=True)
    user = fields.Nested(UserResponseSchema, dump_only=True)


# Schema instances
register_schema = RegisterSchema()
login_schema = LoginSchema()
user_response_schema = UserResponseSchema()
auth_response_schema = AuthResponseSchema()