"""Authentication service for business logic."""
from app.extensions import db
from app.models.user import User, UserRole
from app.models.enums import UserRole as UserRoleEnum
from app.models.student_profile import StudentProfile


class AuthService:
    """Service layer for authentication operations."""

    @staticmethod
    def register_user(email: str, password: str, first_name: str, last_name: str, role: str = "STUDENT") -> User:
        """Register a new user."""
        email = email.strip().lower()

        if User.query.filter_by(email=email).first():
            raise ValueError("Email already registered")

        try:
            user_role = UserRoleEnum(role.upper())
        except ValueError:
            raise ValueError(f"Invalid role. Must be one of: {', '.join(UserRoleEnum.list())}")

        user = User(
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            role=user_role
        )

        db.session.add(user)
        db.session.flush()
        if user.has_role("STUDENT"):
            db.session.add(StudentProfile(user_id=user.id, full_name=user.full_name))
        db.session.commit()
        return user

    @staticmethod
    def authenticate_user(email: str, password: str) -> User:
        """Authenticate user and return user object if valid."""
        email = email.strip().lower()
        user = User.query.filter_by(email=email, is_active=True).first()

        if not user:
            raise ValueError("Invalid email or password")

        if not user.check_password(password):
            raise ValueError("Invalid email or password")

        return user

    @staticmethod
    def get_user_by_id(user_id: int) -> User:
        """Get user by ID."""
        return User.query.filter_by(id=user_id, is_active=True).first()

    @staticmethod
    def get_user_by_email(email: str) -> User:
        """Get user by email."""
        return User.query.filter_by(email=email.strip().lower(), is_active=True).first()
