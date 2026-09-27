"""User model for authentication and RBAC."""
from datetime import datetime, timezone
from werkzeug.security import generate_password_hash, check_password_hash
from app.extensions import db
from app.models.enums import UserRole


class User(db.Model):
    """User database model."""
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    role = db.Column(
        db.Enum(UserRole, name="user_roles", native_enum=False, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        default=UserRole.STUDENT,
        index=True
    )
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    def __init__(self, email, password, first_name, last_name, role=UserRole.STUDENT, is_active=True):
        self.email = email.strip().lower()
        self.set_password(password)
        self.first_name = first_name.strip()
        self.last_name = last_name.strip()
        if isinstance(role, str):
            self.role = UserRole(role.upper())
        else:
            self.role = role
        self.is_active = is_active

    def set_password(self, password: str) -> None:
        """Hash and set user password."""
        if not password:
            raise ValueError("Password cannot be empty")
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        """Verify user password against stored hash."""
        if not password or not self.password_hash:
            return False
        return check_password_hash(self.password_hash, password)

    def has_role(self, *roles) -> bool:
        """Check if user has any of the specified roles."""
        role_values = [r.value if isinstance(r, UserRole) else str(r).upper() for r in roles]
        current_role_value = self.role.value if isinstance(self.role, UserRole) else str(self.role).upper()
        return current_role_value in role_values

    @property
    def full_name(self) -> str:
        """Return user's full name."""
        return f"{self.first_name} {self.last_name}".strip()

    def to_dict(self) -> dict:
        """Serialize user object to dictionary (excluding sensitive data)."""
        role_val = self.role.value if isinstance(self.role, UserRole) else str(self.role)
        return {
            "id": self.id,
            "email": self.email,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "full_name": self.full_name,
            "role": role_val,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def __repr__(self) -> str:
        return f"<User {self.id}: {self.email} ({self.role})>"
