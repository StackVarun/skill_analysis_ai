"""Skill service for business logic."""
from app.extensions import db
from app.models.skill import Skill


class SkillService:
    """Service layer for skill operations."""

    @staticmethod
    def get_all_skills(category=None, search=None):
        """Get all skills with optional filtering."""
        query = Skill.query

        if category:
            query = query.filter(Skill.category.ilike(f"%{category}%"))

        if search:
            query = query.filter(
                db.or_(
                    Skill.name.ilike(f"%{search}%"),
                    Skill.description.ilike(f"%{search}%")
                )
            )

        return query.order_by(Skill.name).all()

    @staticmethod
    def get_skill_by_id(skill_id: int):
        """Get skill by ID."""
        return Skill.query.filter_by(id=skill_id).first()

    @staticmethod
    def get_skill_by_name(name: str):
        """Get skill by name (case-insensitive)."""
        return Skill.query.filter(db.func.lower(Skill.name) == name.lower().strip()).first()

    @staticmethod
    def create_skill(name: str, category: str = None, description: str = None) -> Skill:
        """Create a new skill."""
        # Check for duplicate
        existing = SkillService.get_skill_by_name(name)
        if existing:
            raise ValueError(f"Skill '{name}' already exists")

        skill = Skill(name=name, category=category, description=description)
        db.session.add(skill)
        db.session.commit()
        return skill

    @staticmethod
    def update_skill(skill_id: int, data: dict) -> Skill:
        """Update an existing skill."""
        skill = Skill.query.filter_by(id=skill_id).first()
        if not skill:
            raise ValueError("Skill not found")

        # Check for duplicate name if name is being updated
        if "name" in data and data["name"] != skill.name:
            existing = SkillService.get_skill_by_name(data["name"])
            if existing:
                raise ValueError(f"Skill '{data['name']}' already exists")

        for key, value in data.items():
            if hasattr(skill, key) and key not in ("id", "created_at"):
                setattr(skill, key, value)

        db.session.commit()
        return skill

    @staticmethod
    def delete_skill(skill_id: int) -> bool:
        """Delete a skill."""
        skill = Skill.query.filter_by(id=skill_id).first()
        if not skill:
            return False
        db.session.delete(skill)
        db.session.commit()
        return True