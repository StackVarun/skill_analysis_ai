"""Routes package initialization."""
from app.routes.auth_routes import auth_bp
from app.routes.test_routes import test_bp

__all__ = ["auth_bp", "test_bp"]