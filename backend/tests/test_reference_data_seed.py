from app.extensions import db
from app.models.role import Role, RoleSkillRequirement
from app.models.skill import Skill
from app.models.user import User
from app.services.reference_data_service import ReferenceDataService, SKILL_CATALOG


def test_reference_data_seed_is_repeatable_and_keeps_existing_records(app, student_user_id):
    with app.app_context():
        existing_python = Skill(name="python", category="Existing")
        db.session.add(existing_python)
        db.session.commit()
        python_id = existing_python.id

        first = ReferenceDataService.seed()
        seeded_skill_count = Skill.query.count()
        seeded_role_count = Role.query.count()
        seeded_requirement_count = RoleSkillRequirement.query.count()
        second = ReferenceDataService.seed()

        assert first["skills_added"] == len(SKILL_CATALOG) - 1
        assert first["roles_added"] == 7
        assert first["requirements_added"] > 0
        assert second["skills_added"] == second["roles_added"] == second["requirements_added"] == 0
        assert Skill.query.count() == seeded_skill_count
        assert Role.query.count() == seeded_role_count == 7
        assert RoleSkillRequirement.query.count() == seeded_requirement_count
        assert Skill.query.get(python_id).name == "python"
        assert Skill.query.filter(db.func.lower(Skill.name) == "python").count() == 1
        assert any(role.name == "Machine Learning Engineer" for role in Role.query.all())
        assert User.query.get(student_user_id) is not None
