"""Seed the initial skills and roles into the configured application database."""
from app import create_app
from app.services.reference_data_service import ReferenceDataService


def main():
    app = create_app()
    with app.app_context():
        result = ReferenceDataService.seed()
        print(
            "Reference data seed complete: "
            f"{result['skills_added']} skills, "
            f"{result['roles_added']} roles, "
            f"{result['requirements_added']} role requirements added."
        )


if __name__ == "__main__":
    main()
