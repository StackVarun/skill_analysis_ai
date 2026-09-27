"""Authentication routes."""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_current_user
from marshmallow import ValidationError

from app.services.auth_service import AuthService
from app.schemas.auth_schema import register_schema, login_schema, auth_response_schema, user_response_schema


auth_bp = Blueprint("auth", __name__, url_prefix="/")


@auth_bp.route("/register", methods=["POST"])
def register():
    """Register a new user."""
    try:
        data = register_schema.load(request.get_json() or {})
    except ValidationError as err:
        return jsonify({"error": "Validation error", "messages": err.messages}), 400

    try:
        user = AuthService.register_user(
            email=data["email"],
            password=data["password"],
            first_name=data["first_name"],
            last_name=data["last_name"],
            role=data.get("role", "STUDENT")
        )
    except ValueError as e:
        return jsonify({"error": "Registration failed", "message": str(e)}), 400

    access_token = create_access_token(identity=user)
    response_data = {
        "access_token": access_token,
        "user": user.to_dict()
    }

    return jsonify(auth_response_schema.dump(response_data)), 201


@auth_bp.route("/login", methods=["POST"])
def login():
    """Authenticate user and return access token."""
    try:
        data = login_schema.load(request.get_json() or {})
    except ValidationError as err:
        return jsonify({"error": "Validation error", "messages": err.messages}), 400

    try:
        user = AuthService.authenticate_user(data["email"], data["password"])
    except ValueError as e:
        return jsonify({"error": "Authentication failed", "message": str(e)}), 401

    access_token = create_access_token(identity=user)
    response_data = {
        "access_token": access_token,
        "user": user.to_dict()
    }

    return jsonify(auth_response_schema.dump(response_data)), 200


@auth_bp.route("/me", methods=["GET"])
@jwt_required()
def get_current_user_info():
    """Get current authenticated user's information."""
    current_user = get_current_user()

    if not current_user:
        return jsonify({"error": "User not found", "message": "User account not found"}), 404

    return jsonify(user_response_schema.dump(current_user.to_dict())), 200