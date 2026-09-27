"""RBAC decorators for role-based access control."""
from functools import wraps
from flask import jsonify
from flask_jwt_extended import verify_jwt_in_request, get_current_user


def roles_required(*allowed_roles):
    """
    Decorator to restrict access to specific roles.
    
    Usage:
        @roles_required("STUDENT", "INSTITUTION")
        def some_endpoint():
            ...
    """
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            verify_jwt_in_request()
            current_user = get_current_user()

            if current_user is None:
                return jsonify({"error": "User not found", "message": "User account not found"}), 404

            if not current_user.is_active:
                return jsonify({"error": "Account deactivated", "message": "Your account has been deactivated"}), 403

            role_values = [role.upper() for role in allowed_roles]
            current_role = current_user.role.value if hasattr(current_user.role, 'value') else str(current_user.role).upper()

            if current_role not in role_values:
                return jsonify({
                    "error": "Forbidden",
                    "message": f"Access denied. Required roles: {', '.join(role_values)}"
                }), 403

            return fn(*args, **kwargs)
        return wrapper
    return decorator


def student_required(fn):
    """Decorator to restrict access to students only."""
    return roles_required("STUDENT")(fn)


def industry_required(fn):
    """Decorator to restrict access to industry users only."""
    return roles_required("INDUSTRY")(fn)


def academician_required(fn):
    """Decorator to restrict access to academicians only."""
    return roles_required("ACADEMICIAN")(fn)


def institution_required(fn):
    """Decorator to restrict access to institutions only."""
    return roles_required("INSTITUTION")(fn)


def any_authenticated_user(fn):
    """Decorator to allow any authenticated user (all roles)."""
    return roles_required("STUDENT", "INDUSTRY", "ACADEMICIAN", "INSTITUTION")(fn)