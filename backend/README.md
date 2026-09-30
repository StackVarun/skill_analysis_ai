# SkillBridge AI - Backend

Backend API for SkillBridge AI - A centralized Academia-Industry Collaboration Portal.

## Tech Stack

- **Python** 3.11+
- **Flask** 3.0+
- **Flask-SQLAlchemy** 3.1+
- **Flask-Migrate** 4.0+
- **Flask-JWT-Extended** 4.6+
- **Flask-CORS** 4.0+
- **Marshmallow** 3.20+
- **SQLite** (development)

## Project Structure

```
backend/
├── app/
│   ├── __init__.py          # Flask app factory
│   ├── config.py            # Configuration management
│   ├── extensions.py        # Flask extensions
│   ├── models/              # SQLAlchemy models
│   │   ├── __init__.py
│   │   ├── enums.py         # UserRole enum
│   │   └── user.py          # User model
│   ├── routes/              # API routes
│   │   ├── __init__.py
│   │   ├── auth_routes.py   # Authentication endpoints
│   │   └── test_routes.py   # RBAC test endpoints
│   ├── schemas/             # Validation schemas
│   │   └── auth_schema.py
│   ├── services/            # Business logic
│   │   └── auth_service.py
│   └── utils/               # Utilities
│       └── decorators.py    # RBAC decorators
├── migrations/              # Database migrations
├── config.py                # Root config
├── extensions.py            # Root extensions
├── run.py                   # Entry point
├── requirements.txt
└── .env.example
```

## API Endpoints

### Authentication
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/register` | Register new user |
| POST | `/api/auth/login` | Login and get JWT token |
| GET | `/api/auth/me` | Get current user info (protected) |

### RBAC Test Endpoints
| Method | Endpoint | Access |
|--------|----------|--------|
| GET | `/api/test/public` | Public |
| GET | `/api/test/protected` | Any authenticated user |
| GET | `/api/test/student-only` | STUDENT only |
| GET | `/api/test/industry-only` | INDUSTRY only |
| GET | `/api/test/academician-only` | ACADEMICIAN only |
| GET | `/api/test/institution-only` | INSTITUTION only |
| GET | `/api/test/student-or-institution` | STUDENT or INSTITUTION |
| GET | `/api/test/industry-or-academician` | INDUSTRY or ACADEMICIAN |

### Health Check
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |

## User Roles

- **STUDENT** - Students seeking placements
- **INDUSTRY** - Industry professionals/companies
- **ACADEMICIAN** - Faculty/academic staff
- **INSTITUTION** - Educational institutions

## Setup

### Prerequisites
- Python 3.11+
- pip

### Installation

1. Navigate to backend directory:
```bash
cd backend
```

2. Create virtual environment:
```bash
python -m venv .venv
```

3. Activate virtual environment:
```bash
# Windows
.venv\Scripts\activate

# Linux/Mac
source .venv/bin/activate
```

4. Install dependencies:
```bash
pip install -r requirements.txt
```

5. Copy environment file:
```bash
copy .env.example .env
```

6. Initialize database:
```bash
flask db upgrade
```

### Running the Server

```bash
# Development
flask run --port 5001 --debug

# Or using run.py
python run.py
```

The server will start at `http://localhost:5001`

## Testing the API

### Register a new user
```bash
curl -X POST http://localhost:5001/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "student@example.com",
    "password": "password123",
    "first_name": "John",
    "last_name": "Doe",
    "role": "STUDENT"
  }'
```

### Login
```bash
curl -X POST http://localhost:5001/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "student@example.com",
    "password": "password123"
  }'
```

### Get current user (protected)
```bash
curl -X GET http://localhost:5001/api/auth/me \
  -H "Authorization: Bearer <your_access_token>"
```

### Test RBAC endpoints
```bash
# Public endpoint
curl http://localhost:5001/api/test/public

# Protected endpoint (requires token)
curl -H "Authorization: Bearer <your_access_token>" \
  http://localhost:5001/api/test/protected

# Role-specific endpoint
curl -H "Authorization: Bearer <your_student_token>" \
  http://localhost:5001/api/test/student-only
```

## Database Migrations

```bash
# Create new migration
flask db migrate -m "Description of changes"

# Apply migrations
flask db upgrade

# Rollback migration
flask db downgrade
```

## Configuration

Environment variables (from `.env`):
- `FLASK_ENV` - Environment (development/testing/production)
- `SECRET_KEY` - Flask secret key
- `JWT_SECRET_KEY` - JWT signing key
- `JWT_ACCESS_TOKEN_EXPIRES_HOURS` - Token expiry in hours
- `DATABASE_URL` - Database connection string
- `CORS_ORIGINS` - Comma-separated allowed origins
- `PORT` - Server port

## Security

- Passwords are hashed using Werkzeug's `generate_password_hash`
- JWT tokens for stateless authentication
- Role-based access control (RBAC) on protected endpoints
- CORS configured for frontend integration

## Testing

Run tests:
```bash
pytest
```

## Phase 3 Skill Intelligence

Protected endpoints expose assessments, skill scores, role requirements, role matches, skill gaps, and rule based learning recommendations under `/api`. Assessment and role authoring require an authenticated industry, academician, or institution account for assessments and an institution account for roles. Student analysis and assessment attempts are scoped to the authenticated student's profile.

Assessment score is `correct answers / total questions * 100`. Skill proficiency uses the mean assessment score blended with the existing self reported proficiency level at 70% and 30%; when only one source exists, that source is used. Evidence score adds configured evidence type weights adjusted by evidence strength, applies a configurable multiplier to verified evidence, then caps the result at 100. Overall skill score is the normalized weighted mean of proficiency and evidence (defaults 60% / 40%). Role match is the weighted mean of each required skill's overall score. Gap is `max(0, required score - overall skill score)`, classified at configurable minor and moderate thresholds. Recommendations use configurable topic lists in `app/services/skill_intelligence_service.py` and sort missing/large gaps first.

Tune scoring and gap thresholds with `SKILL_PROFICIENCY_WEIGHT`, `SKILL_EVIDENCE_WEIGHT`, `SKILL_EVIDENCE_VERIFIED_MULTIPLIER`, and the `Config` values in `config.py`. Apply the schema migration with `flask db upgrade`.

### Seed initial skill and role reference data

After applying migrations, run the repeatable seed command from the `backend` directory:

```bash
python seed_reference_data.py
```

It uses the database configured by `DATABASE_URL` (or the default `database/skillbridge.db`) to add missing skills, seven common target roles, and their weighted skill requirements. It does not remove or overwrite existing catalog records, requirements, or student data. The protected `POST /api/roles/seed` endpoint uses the same seed data.

## Phase 4A Optional Local AI

Phase 4A adds four authenticated student endpoints:

- `POST /api/ai/resume-skills/extract` with `{ "resume_id": 1 }`
- `POST /api/ai/skills/normalize` with `{ "variant": "JS" }`
- `POST /api/ai/skill-gaps/explain` with `{ "role_id": 1 }`
- `POST /api/ai/learning-roadmap` with `{ "role_id": 1 }`

The route layer calls `LocalAIService`, which uses a replaceable `OllamaAdapter`. The adapter calls Ollama's local `127.0.0.1:11434` HTTP API using Python's standard library; no model package, external AI API, or API key is required by the backend. The default model is `qwen2.5:1.5b-instruct-q5_0` (about 1.1 GB). To enable generation on Windows, install Ollama from [ollama.com/download/windows](https://ollama.com/download/windows), then run:

```powershell
ollama run qwen2.5:1.5b-instruct-q5_0
```

Set `LOCAL_AI_BASE_URL`, `LOCAL_AI_MODEL`, and `LOCAL_AI_TIMEOUT_SECONDS` in the environment to change the local server, model, or timeout. Flask startup never loads or requires the model. If the runtime/model is missing, fails, times out, returns malformed output, or returns output that fails validation, the endpoint reports `status: "fallback"` and provides a deterministic catalog/Phase 3 based result when possible.

Resume extraction only returns catalog skills supported by source text, labels them as unverified suggestions, and never writes them to student skills. Normalization suggestions must resolve to an existing skill. Gap explanations and roadmaps consume the Phase 3 result; the service preserves the numeric scores, gaps, and role match and does not ask the model to compute them. Unit and API tests mock the adapter and do not download a model.

## Phase 5A: industry and opportunities

An INDUSTRY user's existing `User` identity and one owned `CompanyProfile` form
its industry profile. Company fields are `name`, `website`, `description`, and
`location`. Save/read them with `PUT/GET /api/industry/company`.

| Endpoint | Access and behavior |
| --- | --- |
| `GET /api/opportunities` | STUDENT: open postings; INDUSTRY: own postings, including closed ones |
| `POST /api/opportunities` | INDUSTRY with a company profile: create a posting |
| `GET /api/opportunities/:id` | STUDENT: open posting; INDUSTRY: own posting |
| `PUT /api/opportunities/:id` | Owning INDUSTRY: edit fields and replace skill requirements |
| `DELETE /api/opportunities/:id` | Owning INDUSTRY: close posting, preserving applications |
| `POST /api/opportunities/:id/apply` | STUDENT with a profile: apply once |
| `GET /api/applications/mine` | STUDENT: own application statuses and posting details |
| `GET /api/opportunities/:id/applications` | Owning INDUSTRY: applicants, profiles and deterministic matches |
| `GET /api/applications/:id` | Owning INDUSTRY: one candidate's profile and match details |
| `POST /api/applications/:id/shortlist` | Owning INDUSTRY: shortlist an eligible application |
| `PATCH /api/applications/:id/status` | Owning INDUSTRY: advance application status |
| `GET /api/industry/summary` | INDUSTRY: own posting and application counts |

All endpoints require JWT authentication. Faculty and institution accounts cannot
access these APIs. Institutional aggregate analytics remain a separate API.
Owner IDs, applicant IDs and scores are derived on the server, never accepted as
posting inputs. Unknown input fields are rejected.

Posting JSON example (replace the skill ID with a catalog ID and the deadline
with a future date):

```json
{
  "title": "Backend internship",
  "description": "Build and test Python web services.",
  "kind": "INTERNSHIP",
  "location": "Chennai",
  "employment_type": "FULL_TIME",
  "eligibility": "CSE students graduating in 2029",
  "deadline": "2027-06-30",
  "stipend": "INR 15001/month",
  "duration": "12 weeks",
  "required_skills": [
    {"skill_id": 1, "required_proficiency": 70, "weight": 2}
  ]
}
```

Use `kind: "JOB"` for job postings. Title, description, kind and at least one
required skill are mandatory. Other fields are optional to preserve the existing
frontend contract. Eligibility is recruiter-provided descriptive text, not an
automated eligibility decision. Employment type is a bounded text field. Skill
IDs must exist and be unique within a posting. Scores are finite numbers in
0–100 and weights in 0.001–100. Blank titles/descriptions, past deadlines,
malformed JSON and invalid requirements return 400 without changing the posting.
Deadlines are inclusive, using the backend server's calendar date.

Applications start at `APPLIED`. Valid forward transitions:

- APPLIED → REVIEWING, SHORTLISTED, REJECTED
- REVIEWING → SHORTLISTED, INTERVIEW, REJECTED
- SHORTLISTED → INTERVIEW, OFFER, REJECTED
- INTERVIEW → OFFER, REJECTED
- OFFER and REJECTED are final; repeating the current status is idempotent.

Duplicate applications return 409 and have a database unique constraint as a
second guard against concurrent submissions. Closed/expired opportunities reject
new applications; existing applications remain visible in student tracking.

Matching uses a transient Role adapter and calls the existing
`SkillIntelligenceService.analyze_role` exactly once per candidate. The response
retains its `match_percentage`, weighted `required_skills`, `skill_gaps`, and
`missing_skills`. `matching_skills` contains requirements with zero gap. Evidence
includes stored titles, source URLs, verification labels and linked record IDs;
relevant projects, experience and internships use existing skill associations.
No Role records are created, and no AI service or second scoring formula is used.
Matches are computed from the candidate's current data and current posting
requirements, rather than a historical snapshot at application time.

The existing migration `6a29c9a56b71` provides all Phase 5A tables. This completion
adds no schema changes. From `backend/`, use `python -m flask --app run.py db upgrade`
for databases that have not yet applied that migration. Run
`python -m pytest tests/test_industry_opportunities.py -q` for targeted checks and
`python -m pytest -q` for the full regression suite.
