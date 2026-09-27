"""Test routes for RBAC verification."""
from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_current_user

from app.utils.decorators import (
    roles_required,
    student_required,
    industry_required,
    academician_required,
    institution_required,
    any_authenticated_user
)


test_bp = Blueprint("test", __name__, url_prefix="/")


@test_bp.route("/public", methods=["GET"])
def public_endpoint():
    """Public endpoint - no authentication required."""
    return jsonify({
        "message": "This is a public endpoint",
        "access": "public"
    }), 200


@test_bp.route("/protected", methods=["GET"])
@jwt_required()
def protected_endpoint():
    """Protected endpoint - requires valid JWT token (any role)."""
    current_user = get_current_user()
    return jsonify({
        "message": "This is a protected endpoint",
        "access": "authenticated",
        "user": current_user.to_dict()
    }), 200


@test_bp.route("/student-only", methods=["GET"])
@student_required
def student_only_endpoint():
    """Endpoint accessible only by STUDENT role."""
    current_user = get_current_user()
    return jsonify({
        "message": "Student only endpoint",
        "access": "STUDENT",
        "user": current_user.to_dict()
    }), 200


@test_bp.route("/industry-only", methods=["GET"])
@industry_required
def industry_only_endpoint():
    """Endpoint accessible only by INDUSTRY role."""
    current_user = get_current_user()
    return jsonify({
        "message": "Industry only endpoint",
        "access": "INDUSTRY",
        "user": current_user.to_dict()
    }), 200


@test_bp.route("/academician-only", methods=["GET"])
@academician_required
def academician_only_endpoint():
    """Endpoint accessible only by ACADEMICIAN role."""
    current_user = get_current_user()
    return jsonify({
        "message": "Academician only endpoint",
        "access": "ACADEMICIAN",
        "user": current_user.to_dict()
    }), 200


@test_bp.route("/institution-only", methods=["GET"])
@institution_required
def institution_only_endpoint():
    """Endpoint accessible only by INSTITUTION role."""
    current_user = get_current_user()
    return jsonify({
        "message": "Institution only endpoint",
        "access": "INSTITUTION",
        "user": current_user.to_dict()
    }), 200


@test_bp.route("/student-or-institution", methods=["GET"])
@roles_required("STUDENT", "INSTITUTION")
def student_or_institution_endpoint():
    """Endpoint accessible by STUDENT or INSTITUTION roles."""
    current_user = get_current_user()
    return jsonify({
        "message": "Student or Institution endpoint",
        "access": "STUDENT, INSTITUTION",
        "user": current_user.to_dict()
    }), 200


@test_bp.route("/industry-or-academician", methods=["GET"])
@roles_required("INDUSTRY", "ACADEMICIAN")
def industry_or_academician_endpoint():
    """Endpoint accessible by INDUSTRY or ACADEMICIAN roles."""
    current_user = get_current_user()
    return jsonify({
        "message": "Industry or Academician endpoint",
        "access": "INDUSTRY, ACADEMICIAN",
        "user": current_user.to_dict()
    }), 200