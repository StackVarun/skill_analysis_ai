"""Idempotent seed data for the skill catalog and target roles."""
from app.extensions import db
from app.models.role import Role, RoleSkillRequirement
from app.models.skill import Skill


SKILL_CATALOG = (
    ("Python", "Programming", "General-purpose programming with Python."),
    ("Java", "Programming", "Object-oriented programming with Java."),
    ("C++", "Programming", "Systems and application programming with C++."),
    ("JavaScript", "Programming", "Programming for web applications."),
    ("TypeScript", "Programming", "Typed JavaScript for web applications."),
    ("SQL", "Data", "Querying and managing relational databases."),
    ("HTML", "Web Development", "Semantic structure for web pages."),
    ("CSS", "Web Development", "Styling and layout for web interfaces."),
    ("React", "Web Development", "Component-based user interface development."),
    ("Node.js", "Web Development", "Server-side JavaScript development."),
    ("Express.js", "Web Development", "Web application framework for Node.js."),
    ("Flask", "Web Development", "Lightweight Python web application framework."),
    ("REST APIs", "Web Development", "Designing and building RESTful APIs."),
    ("Git", "Tools", "Version control with Git."),
    ("GitHub", "Tools", "Collaborative software development using GitHub."),
    ("Data Structures", "Computer Science", "Common structures for organizing and accessing data."),
    ("Algorithms", "Computer Science", "Design and analysis of computational algorithms."),
    ("Database Management", "Data", "Relational database design and management."),
    ("Machine Learning", "Data Science", "Building and evaluating machine learning models."),
    ("Data Analysis", "Data Science", "Inspecting, cleaning, and interpreting data."),
    ("Statistics", "Data Science", "Statistical reasoning and quantitative analysis."),
    ("Data Visualization", "Data Science", "Communicating data insights through visualizations."),
    ("Excel", "Data", "Spreadsheet analysis and reporting."),
)

# Each entry is (skill name, required proficiency, relative match weight).
# Keep requirements explicit because the existing schema has no OR/alternative
# requirement representation.
ROLE_CATALOG = {
    "Software Engineer": [
        ("Python", 70, 1.0), ("Data Structures", 75, 1.3),
        ("Algorithms", 75, 1.3), ("SQL", 65, 0.8), ("Git", 65, 0.8),
    ],
    "Backend Developer": [
        ("Python", 70, 1.0), ("Flask", 70, 1.0), ("REST APIs", 75, 1.2),
        ("SQL", 70, 1.0), ("Git", 65, 0.8),
    ],
    "Frontend Developer": [
        ("JavaScript", 75, 1.2), ("TypeScript", 65, 0.8),
        ("HTML", 70, 1.0), ("CSS", 70, 1.0), ("React", 75, 1.2), ("Git", 65, 0.8),
    ],
    "Full Stack Developer": [
        ("JavaScript", 70, 1.0), ("React", 70, 1.0), ("Node.js", 70, 1.0),
        ("Express.js", 65, 0.8), ("SQL", 65, 0.8), ("REST APIs", 70, 1.0),
        ("Git", 65, 0.8),
    ],
    "Data Analyst": [
        ("SQL", 75, 1.2), ("Python", 65, 0.8), ("Data Analysis", 75, 1.2),
        ("Statistics", 70, 1.0), ("Data Visualization", 70, 1.0), ("Excel", 65, 0.8),
    ],
    "Data Scientist": [
        ("Python", 75, 1.0), ("SQL", 65, 0.8), ("Statistics", 75, 1.1),
        ("Machine Learning", 80, 1.3), ("Data Analysis", 70, 0.9),
        ("Data Visualization", 65, 0.8),
    ],
    "Machine Learning Engineer": [
        ("Python", 80, 1.2), ("Machine Learning", 80, 1.3),
        ("Data Structures", 70, 0.9), ("Algorithms", 75, 1.0),
        ("SQL", 65, 0.7), ("Git", 65, 0.7),
    ],
}


class ReferenceDataService:
    """Create missing catalog data without changing user or existing reference data."""

    @staticmethod
    def seed():
        skills = {
            skill.name.strip().casefold(): skill
            for skill in Skill.query.order_by(Skill.id).all()
        }
        skills_added = 0
        for name, category, description in SKILL_CATALOG:
            key = name.casefold()
            if key not in skills:
                skill = Skill(name=name, category=category, description=description)
                db.session.add(skill)
                skills[key] = skill
                skills_added += 1

        roles = {
            role.name.strip().casefold(): role
            for role in Role.query.order_by(Role.id).all()
        }
        roles_added = 0
        requirements_added = 0
        # Flush once so newly added catalog rows have IDs before relationships
        # are created. Existing rows are never edited or removed.
        db.session.flush()
        for name, requirements in ROLE_CATALOG.items():
            role = roles.get(name.casefold())
            if role is None:
                role = Role(name=name, description=f"Core skills for a {name}.")
                db.session.add(role)
                db.session.flush()
                roles[name.casefold()] = role
                roles_added += 1

            existing_skill_ids = {item.skill_id for item in role.requirements}
            for skill_name, proficiency, weight in requirements:
                skill = skills[skill_name.casefold()]
                if skill.id in existing_skill_ids:
                    continue
                role.requirements.append(RoleSkillRequirement(
                    skill_id=skill.id,
                    required_proficiency=proficiency,
                    weight=weight,
                ))
                existing_skill_ids.add(skill.id)
                requirements_added += 1

        db.session.commit()
        return {
            "skills_added": skills_added,
            "roles_added": roles_added,
            "requirements_added": requirements_added,
            "roles": Role.query.order_by(Role.name).all(),
        }
