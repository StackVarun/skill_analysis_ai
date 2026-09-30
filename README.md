# SkillBridge AI

A Flask + SQLite backend and React + Vite frontend connecting student skills to industry opportunities. Phase 3 provides deterministic scoring. The optional local Ollama layer explains results without changing scores.

## Run locally

1. `cd backend && python -m pip install -r requirements.txt`
2. Copy `backend/.env.example` to `backend/.env`; set strong `SECRET_KEY` and `JWT_SECRET_KEY`. The default database is `database/skillbridge.db`.
3. From `backend/`: `python -m flask --app run.py db upgrade`, then `python seed_reference_data.py` if role/skill catalogs are empty.
4. Optional demo: `DEMO_PASSWORD='choose-a-local-demo-password' python seed_demo.py --reset-passwords`. It creates the four demo role logins and reuses the five `student1@test.com` through `student5@test.com` accounts, adding missing skill/portfolio data and submitting their applications. The reset flag updates only these named demo/test accounts. Existing portfolios, job requirements, owners and application statuses are preserved.
5. From `backend/`: `python run.py`.
6. From `frontend/`: `npm install && npm run dev`. Open `http://localhost:5173`.

The Vite development server proxies `/api` to Flask on port 5001 by default and follows `PORT` from the root/backend `.env`. Use `API_PROXY_TARGET` in the frontend environment for an explicit override. On macOS, port 5000 may be occupied by AirPlay; use port 5001 and restart both servers. Keep `VITE_API_BASE_URL=/api` for local development. For a separate frontend deployment, set `VITE_API_BASE_URL` to the full API URL and configure `CORS_ORIGINS` on the backend. The Ollama runtime is optional; see `backend/README.md` for local AI configuration and resume support.

Institution accounts are provisioned locally with `INSTITUTION_EMAIL=... INSTITUTION_PASSWORD=... INSTITUTION_NAME=... python provision_institution.py` from `backend/`; public registration allows student, industry and academician accounts. Institution reports are scoped to the provisioned institution name.

## Architecture and API

`frontend/src/services/api.js` → Flask routes → validation / services → SQLAlchemy models → SQLite. Candidate scores call the original `SkillIntelligenceService.analyze_role` using a posting's skill requirements. No generated text sets numeric scores.

| Role | Main endpoints |
| --- | --- |
| Student | `GET /api/opportunities`, `POST /api/opportunities/:id/apply`, `GET /api/applications/mine`, `GET /api/passport/me` |
| Industry | `GET/PUT /api/industry/company`, `GET/POST /api/opportunities`, `GET/PUT/DELETE /api/opportunities/:id`, `GET /api/opportunities/:id/applications`, `POST /api/applications/:id/shortlist`, `GET /api/industry/summary` |
| Academician | `GET/PUT /api/faculty/profile`, `GET/POST /api/faculty/opportunities`, `GET /api/faculty/applications/mine`, `POST /api/faculty/opportunities/:id/apply` |
| Institution | `GET /api/institution/analytics` (aggregate, scoped to its registered institution) |

Existing auth, profile, assessment, skill, portfolio, role matching and AI endpoints remain documented in `backend/README.md`. Faculty posting and application management also have owner scoped PUT/DELETE, applicant listing and shortlist endpoints in `faculty_routes.py`.

## Demo flow

Run the demo seed → sign in as the owning industry account printed by the script → click **View applicants** → compare five students ranked by weighted skill score, inspect their targets/gaps and portfolio evidence, then shortlist. Sign in as faculty to inspect the FDP opportunity or as institution to inspect aggregate gaps and demand. Add resume and assessment data through the student workspace to demonstrate the full phase 1–4 flow.

## Verification

From `backend/`: `python -m pytest -q`. From `frontend/`: `npm test && npm run build`. Run `python -m flask --app run.py db upgrade` for the database migration.

## Limits

The demo seeds a small data set. Placement readiness is the mean of available student to role matches, and industry demand sums posting weights. These are descriptive aggregates, not a predictive hiring model. Publicly self-registered industry/academician accounts are unverified; use trusted demo users only. The role dashboards use the project's existing CSS and native charts; Tailwind, shadcn/ui and Recharts are not dependencies in the supplied codebase.

## Existing posting and login troubleshooting

The seed automatically uses the only open job. If there are several jobs, or you
want a specific internship, run `DEMO_PASSWORD='your-demo-password' python
seed_demo.py --reset-passwords --opportunity-id 9` from `backend/` (replace 9 with
the actual posting ID). If no job exists it creates a Backend Engineer demo job.
Existing posting ownership is preserved; only its owner can review applicants.
The script prints that owner's email. `student@demo.skillbridge` is an additional
student login for manual exploration; the five applicants use the numbered test
accounts. Missing portfolio entries are synthetic and labelled self reported,
never verified credentials. Existing student skills are not overwritten, so
rankings depend on the actual database data. Repeating the seed does not duplicate
applications or reset hiring decisions.

A wrong password returns a JSON 401 from Flask. A plain 403 at login can indicate
a different server responding at the proxy target. Check `http://localhost:5001/health`
for `SkillBridge AI API`, then confirm the browser is using the same backend.
The starter `.env.example` leaves DATABASE_URL unset, so migrations, seeding and
Flask use `database/skillbridge.db`. If you already set DATABASE_URL, keep that
same database for all three commands; relative SQLite URLs resolve under Flask's
instance directory. Do not switch databases while trying to recover local data.

## Faculty support and student project editing

Students can edit projects in Portfolio and track faculty feedback or assigned
work in Mentorship & reviews. Faculty have a review inbox, student skill-gap
inspection, mentorship allocation, project supervision and current placement
counts. Apply the database migration before starting the updated application.
See [FACULTY_FEATURES.md](FACULTY_FEATURES.md) for setup, behavior and API details.
