"""Flask application factory."""
import os
from flask import Flask, jsonify
from app.extensions import db, migrate, jwt, cors
from app.config import config_by_name


def create_app(config_name=None):
    """Create and configure the Flask application."""
    if config_name is None:
        config_name = os.environ.get("FLASK_ENV", "development")

    app = Flask(__name__)
    app.config.from_object(config_by_name.get(config_name, config_by_name["default"]))

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    cors.init_app(app, origins=app.config["CORS_ORIGINS"])

    # Register JWT callbacks
    register_jwt_callbacks(jwt)

    # Register error handlers
    register_error_handlers(app)

    # Register blueprints
    register_blueprints(app)

    # Health check endpoint
    @app.route("/health")
    def health_check():
        return jsonify({"status": "healthy", "service": "SkillBridge AI API"}), 200

    return app


def register_jwt_callbacks(jwt_manager):
    """Register JWT callback handlers."""
    from app.models.user import User

    @jwt_manager.user_identity_loader
    def user_identity_lookup(user):
        return str(user.id)

    @jwt_manager.user_lookup_loader
    def user_lookup_callback(_jwt_header, jwt_data):
        identity = jwt_data["sub"]
        return User.query.filter_by(id=int(identity), is_active=True).one_or_none()

    @jwt_manager.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        return jsonify({"error": "Token has expired", "message": "Please log in again"}), 401

    @jwt_manager.invalid_token_loader
    def invalid_token_callback(error):
        return jsonify({"error": "Invalid token", "message": "Authentication failed"}), 401

    @jwt_manager.unauthorized_loader
    def missing_token_callback(error):
        return jsonify({"error": "Authorization required", "message": "Please provide a valid token"}), 401

    @jwt_manager.revoked_token_loader
    def revoked_token_callback(jwt_header, jwt_payload):
        return jsonify({"error": "Token revoked", "message": "Token has been revoked"}), 401


def register_error_handlers(app):
    """Register global error handlers."""

    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({"error": "Bad request", "message": str(error)}), 400

    @app.errorhandler(404)
    def not_found(error):
        return jsonify({"error": "Not found", "message": "Resource not found"}), 404

    @app.errorhandler(405)
    def method_not_allowed(error):
        return jsonify({"error": "Method not allowed", "message": "HTTP method not allowed"}), 405

    @app.errorhandler(500)
    def internal_server_error(error):
        return jsonify({"error": "Internal server error", "message": "An unexpected error occurred"}), 500


def register_blueprints(app):
    """Register all blueprints."""
    from app.routes.auth_routes import auth_bp
    from app.routes.test_routes import test_bp
    from app.routes.student_routes import student_bp
    from app.routes.skill_routes import skills_bp
    from app.routes.student_skill_routes import student_skills_bp
    from app.routes.project_routes import projects_bp
    from app.routes.certification_routes import certifications_bp
    from app.routes.experience_routes import experiences_bp
    from app.routes.internship_routes import internships_bp
    from app.routes.skill_evidence_routes import skill_evidence_bp
    from app.routes.resume_routes import resumes_bp

    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(test_bp, url_prefix="/api/test")
    app.register_blueprint(student_bp, url_prefix="/api/students")
    app.register_blueprint(skills_bp, url_prefix="/api")
    app.register_blueprint(student_skills_bp, url_prefix="/api")
    app.register_blueprint(projects_bp, url_prefix="/api")
    app.register_blueprint(certifications_bp, url_prefix="/api")
    app.register_blueprint(experiences_bp, url_prefix="/api")
    app.register_blueprint(internships_bp, url_prefix="/api")
    app.register_blueprint(skill_evidence_bp, url_prefix="/api")
    app.register_blueprint(resumes_bp, url_prefix="/api")