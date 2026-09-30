# Student project editing and faculty support

This update adds project editing and an institution-scoped faculty workflow.
Apply the source update, then run the migration using the same database and Python
environment as the running backend:

```bash
cd backend
python -m flask --app run.py db upgrade
```

Restart Flask and Vite. If needed, use `PORT=5001 python run.py` in backend and
`API_PROXY_TARGET=http://127.0.0.1:5001 VITE_API_BASE_URL=/api npm run dev` in
frontend, in separate terminals. No additional dependencies are required.

## Where to find each feature

| Account | Feature | Where |
| --- | --- | --- |
| Student | Edit existing title, role, technologies, skills, links, description and dates | Portfolio → project → Edit |
| Student | Mark project in progress or completed | Project form → Project status |
| Student | Read faculty feedback and start/submit assigned work | Mentorship & reviews |
| Student | View green marks for faculty endorsements | Skill passport and project cards |
| Academician | Current selected, interview and offer counts | Dashboard cards |
| Academician | Review completed projects, assessment submissions and skill evidence | Verification inbox |
| Academician | View student skills, open gaps and application stages | Student skill gaps & mentorship → Choose student |
| Academician | Allocate targeted coursework or research | Choose student → Allocate mentorship |
| Academician | Supervise a student's project and review milestones | Task type → Project supervision |
| Academician | Complete submitted tasks or return them with feedback | Coursework & research tasks / Project supervision |

Save a faculty institution in **Faculty profile & opportunities**. A student's
profile must have the same institution name, ignoring case and surrounding
spaces, to appear in that faculty workspace. Existing opportunity discovery,
faculty applications and training features remain available below the dashboard.

## Verification behavior

Adding a completed project or submitting an assessment automatically creates a
pending faculty review. Adding skill evidence also creates a verification request.
The faculty inbox refreshes every 30 seconds while visible and can be refreshed
manually. These are notifications inside the application; no email service is
required. Students can see all request statuses and faculty feedback.

Faculty can approve work or request changes. Changes requests require feedback.
Approval records the reviewer and review time. Students can respond to a changes
request and resubmit it, including assessment reviews; resubmission never changes
the scored assessment result. A green passport mark indicates
that the student has faculty-endorsed items; individual skills and projects also
show their own marks. An assessment endorsement confirms faculty review of its
recorded result; it does not change the machine-scored assessment result or
certify that every skill target has been met.

Editing endorsed project content, dates, links or skills resets its review to
pending and removes linked evidence verification. Saving identical content keeps
the existing endorsement. Marking a project in progress withdraws its project
review. The faculty interface sends the version timestamp it displayed so a
review of stale work returns 409 and asks the reviewer to refresh. Multiple faculty
reviewing one pending request cannot both replace the decision.

Student APIs now reject attempts to set evidence to VERIFIED. Editing evidence
resets its faculty review. Legacy stored verification labels do not create green
passport marks: the marks require an actual approved faculty review record.
Project approval verifies evidence for its associated catalog skills, using the
existing evidence weighting rather than a new scoring formula.

The migration adds pending reviews for existing projects, assessment attempts
and skill evidence. Existing projects default to completed; students can change
that through Edit. Their project content, assessment scores and application
statuses are preserved.

## Mentorship and placement counts

Open gaps combine existing role-catalog requirements and requirements from jobs
that the student has applied to. Faculty can attach a skill and optional due date
to coursework/research, or select the student's project for supervision.
Students start work and submit a description or link. Only the assigning faculty
can complete it or return it for revision. Completion does not invent a new skill
score: assessments and portfolio evidence remain the scoring inputs.

Selected students means distinct students with a current SHORTLISTED, INTERVIEW
or OFFER application. Interview and offer cards count distinct students currently
in those stages. These are current-state counts, not historical counts of everyone
who has ever interviewed. A student with several applications can appear in
multiple stages. All counts and student reviews are scoped to the faculty's
institution; mentorship management is also scoped to the assigning faculty.

## API additions

- GET `/api/faculty/summary`
- GET `/api/faculty/students` and `/api/faculty/students/:id`
- GET `/api/faculty/reviews` (optional `status` query)
- POST `/api/faculty/reviews/:id/decision` with decision, feedback, and optional expected_updated_at
- GET/POST `/api/faculty/tasks`
- PATCH `/api/faculty/tasks/:id` for a submitted task
- GET `/api/students/mentorship`
- PATCH `/api/students/mentorship/:id` to start or submit work
- GET `/api/students/reviews`
- POST `/api/students/reviews/:id/resubmit` with a response to faculty feedback

Migration: `b84e21a0f9c3`, after `9d2af314f0c1`. New tables are
verification_requests and mentorship_tasks; projects gain completion_status.

## Verification

The backend tests cover review approvals, badge removal after edits, requested
changes, assessment notifications, student self-verification rejection, stale
review versions, institution access, mentor ownership, student submissions,
project deletion and current placement counts. Frontend tests cover project edit
and cancel, preservation of skill/date data, faculty decisions, task allocation,
student submissions, profile saving and passport marks. A migrated copy of the
existing database was also exercised through the Flask API.
