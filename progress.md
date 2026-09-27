We are building a hackathon project called **SkillBridge AI**.

Build a centralized Academia–Industry Collaboration Portal connecting:

* Students
* Industry
* Academicians
* Institutions

Core goal:

Student skills → assessment → skill analysis → skill gaps → learning → internships/jobs → placement support.

## Tech Stack

Backend:

* Python
* Flask
* Flask REST API
* SQLAlchemy
* SQLite
* JWT authentication

Frontend:

* React + Vite
* Tailwind CSS
* shadcn/ui
* React Router
* Recharts

AI/NLP will be added in later phases.

## Your task: Phase 1 only

Build the backend foundation.

Create a clean structure such as:

backend/
app/
routes/
models/
services/
schemas/
utils/
config.py
extensions.py
run.py
requirements.txt

database/
frontend/

Implement:

1. Flask application setup.
2. SQLAlchemy configuration using SQLite.
3. Database initialization/migrations strategy appropriate for this project.
4. User model.
5. Role-based access control.
6. JWT authentication.
7. Registration and login APIs.
8. Four roles:

   * STUDENT
   * INDUSTRY
   * ACADEMICIAN
   * INSTITUTION
9. Basic protected test endpoint for verifying RBAC.
10. Environment/configuration handling.
11. .env.example.
12. Basic error handling and validation.
13. README instructions for running the backend.

Authentication APIs should include:

POST /api/auth/register
POST /api/auth/login
GET /api/auth/me

Use password hashing. Never store plain-text passwords.

## Important architecture rules

* Keep business logic out of route files where practical.
* Use services for business logic.
* Use SQLAlchemy models for persistence.
* Keep authentication reusable.
* Do not implement student profiles, skill matching, Claude API, assessments, jobs, or dashboards yet.
* Do not add fake functionality.
* Do not create unnecessary dependencies.

## Verification

After implementation:

* Start the Flask server.
* Initialize the SQLite database.
* Test registration.
* Test login.
* Test JWT-protected endpoint.
* Test role restrictions.
* Fix any errors you encounter.

Create/update `progress.md` with:

* completed work
* current phase
* important architecture decisions
* known issues
* next phase

Then show me:

1. Final project structure.
2. APIs created.
3. Database models created.
4. Commands to run the backend.
5. Tests performed.
6. Any known issues.

Do not implement Phase 2.

Stop after Phase 1 is complete.
