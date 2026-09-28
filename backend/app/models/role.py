"""Target roles and their normalized skill requirements."""
from datetime import datetime, timezone
from app.extensions import db


class Role(db.Model):
    __tablename__ = "roles"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), unique=True, nullable=False)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    requirements = db.relationship("RoleSkillRequirement", back_populates="role", cascade="all, delete-orphan")


class RoleSkillRequirement(db.Model):
    __tablename__ = "role_skill_requirements"
    id = db.Column(db.Integer, primary_key=True)
    role_id = db.Column(db.Integer, db.ForeignKey("roles.id", ondelete="CASCADE"), nullable=False, index=True)
    skill_id = db.Column(db.Integer, db.ForeignKey("skills.id", ondelete="RESTRICT"), nullable=False, index=True)
    required_proficiency = db.Column(db.Float, nullable=False)
    weight = db.Column(db.Float, nullable=False, default=1.0)
    role = db.relationship("Role", back_populates="requirements")
    skill = db.relationship("Skill")
    __table_args__ = (db.UniqueConstraint("role_id", "skill_id", name="uq_role_required_skill"), db.CheckConstraint("required_proficiency >= 0 AND required_proficiency <= 100", name="ck_role_required_proficiency"), db.CheckConstraint("weight > 0", name="ck_role_skill_weight"))
