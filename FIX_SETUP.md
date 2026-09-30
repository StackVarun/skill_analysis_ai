# Apply and run the SkillBridge fixes

Prepared against main commit fa49301. These changes cover login/proxy setup,
industry required-skill entry, and a five-applicant demo with company-specific
weighted ranking. GitHub access in this session was read-only, so the patch was
not pushed or deployed.

## Apply the downloaded patch

In your existing repository (not inside backend or frontend):

```bash
git apply --check ~/Downloads/skillbridge-fixes.patch
git apply ~/Downloads/skillbridge-fixes.patch
```

The patch contains source, tests and documentation only. It does not replace
your SQLite database or environment files. If the check reports conflicts,
your code differs from the base revision; do not force the patch.

## Prepare accounts and applicants

Use your existing Python environment and the same DATABASE_URL as the running
app. From the repository root:

```bash
cd backend
python -m flask --app run.py db upgrade
DEMO_PASSWORD='DemoPass123!' python seed_demo.py --reset-passwords
PORT=5001 python run.py
```

If your environment uses python3 instead of python, substitute python3.
The seed uses the only open job already in your database. If several jobs exist,
choose one with `--opportunity-id ACTUAL_ID`. If no job exists, it creates a
Backend Engineer demo job. It preserves posting ownership and requirements.
The script prints the industry account that owns the job: use that account to
review its applications. The four demo role logins are:

- student@demo.skillbridge
- faculty@demo.skillbridge
- industry@demo.skillbridge
- institution@demo.skillbridge

All use DemoPass123! after this explicit reset. Five applications are submitted
from student1@test.com through student5@test.com, using the same password after
reset. Only these named demo/test accounts are reset; unrelated account
passwords are preserved. Existing names and skill data are preserved too.
Missing portfolio data is synthetic, labelled as such, and self reported.
Repeating the command does not duplicate applications or undo hiring statuses.

## Start the frontend

In another terminal, from the repository root:

```bash
cd frontend
API_PROXY_TARGET=http://127.0.0.1:5001 VITE_API_BASE_URL=/api npm run dev
```

Open http://localhost:5173. Stop old Flask/Vite instances before restarting.
The commands above override old port settings for this session. For future
normal starts, set PORT=5001 in the backend/root .env and keep
VITE_API_BASE_URL=/api in the frontend .env. If using a custom port, configure
the proxy to point to it.

## Review candidates

Sign in as the job's owning industry account, click **View applicants**, and
compare the ranked students. The page shows each required skill's target and
weight. Open **View profile** for scores, gaps, projects and evidence; shortlist
the candidate you choose. Rankings use the existing weighted skill-scoring
service and current student data; no automatic hiring decision is made.

The required-skill dropdown now prevents duplicates. Use **Add new skill** if
the catalog is empty or lacks a skill. An existing catalog name is reused.

## If login still fails

Check http://localhost:5001/health. It should return JSON naming
**SkillBridge AI API**. A wrong password returns JSON 401 from Flask; a plain
403 at login suggests a different server/proxy is responding. On macOS, AirPlay
can occupy port 5000, so these instructions use 5001. Official Flask reference:
https://flask.palletsprojects.com/en/stable/server/#address-already-in-use

If accounts are missing, confirm the migration, seed and server all use the
same DATABASE_URL. Relative SQLite URLs resolve under Flask's instance
folder. Keep your current database setting to retain the existing job/data.

## Verification completed

- 117 backend tests passed, including three new demo workflow regressions.
- 27 frontend tests passed, including six new skill/login/ranking regressions.
- Production frontend build succeeded.
- Migrated and seeded a copy of the tracked database successfully.
- Live Vite proxy returned HTTP 200 for all four demo logins and five ranked
  applicants. With the tracked student data, John Doe ranked first at 90;
  scores and ordering on your local database may differ.
