# SkillBridge AI

A Flask + SQLite backend and React + Vite frontend connecting student skills to industry opportunities. Phase 3 provides deterministic scoring. The optional local Ollama layer explains results without changing scores.

## Run locally

1. `cd backend && python -m pip install -r requirements.txt`
2. Copy `backend/.env.example` to `backend/.env`; set strong `SECRET_KEY` and `JWT_SECRET_KEY`. The default database is `database/skillbridge.db`.
3. From `backend/`: `python -m flask --app run.py db upgrade`, then `python seed_reference_data.py` if role/skill catalogs are empty.
4. Optional demo: `DEMO_PASSWORD='choose-a-local-demo-password' python seed_demo.py`. It creates four role accounts and one opportunity; do not use demo accounts in production.
5. From `backend/`: `python run.py`.
6. From `frontend/`: `npm install && npm run dev`. Open `http://localhost:5173`.

The Vite development server proxies `/api` to Flask on port 5000. For a separate frontend deployment, set `VITE_API_BASE_URL` to the full API URL and configure `CORS_ORIGINS` on the backend. The Ollama runtime is optional; see `backend/README.md` for local AI configuration and resume support.

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

Sign in as the demo student → view skill scores and passport → apply to the internship → sign in as industry → inspect deterministic candidate match and shortlist → sign in as faculty → inspect FDP opportunity → sign in as institution → view aggregate skill gaps and demand. Add resume and assessment data through the student workspace to demonstrate the full phase 1–4 flow.

## Verification

From `backend/`: `python -m pytest -q`. From `frontend/`: `npm test && npm run build`. Run `python -m flask --app run.py db upgrade` for the database migration.

## Limits

The demo seeds a small data set. Placement readiness is the mean of available student to role matches, and industry demand sums posting weights. These are descriptive aggregates, not a predictive hiring model. Publicly self-registered industry/academician accounts are unverified; use trusted demo users only. The role dashboards use the project's existing CSS and native charts; Tailwind, shadcn/ui and Recharts are not dependencies in the supplied codebase.
