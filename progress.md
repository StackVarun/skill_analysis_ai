# SkillBridge AI — Progress

## Project

**SkillBridge AI** — Portal for Academia–Industry Collaboration for Skill Mapping, Internships, and Placement.

The system connects:

**Skills → Skill Assessment → Skill Gaps → Learning → Internships → Placement**

---

# Current Phase

## Phase 2 — Student Profile, Skills & Evidence

Phase 1 has been completed and committed.

The current task is to implement Phase 2 only.

Do not redo or rewrite completed Phase 1 functionality unless a genuine bug or dependency requires a small change.

---

# Completed

## Phase 1 — Backend Foundation

* [x] Flask backend foundation
* [x] REST API structure
* [x] SQLite database
* [x] SQLAlchemy integration
* [x] Database migrations setup
* [x] JWT authentication
* [x] User model
* [x] Role definitions
* [x] Role-based access control
* [x] Authentication routes
* [x] Authentication service
* [x] Authentication schemas
* [x] Basic authorization decorators
* [x] Configuration structure
* [x] Environment-variable support
* [x] Basic error handling
* [x] Backend tests
* [x] Basic server startup verification

### User Roles

The system supports:

* `STUDENT`
* `INDUSTRY`
* `ACADEMICIAN`
* `INSTITUTION`

---

# Phase 2 Requirements

## 1. Student Profile

Create the student profile functionality.

A student profile should support information such as:

* Full name
* Email
* Phone
* Institution
* Degree
* Branch / specialization
* Graduation year
* CGPA
* Bio / summary
* Location
* LinkedIn URL
* GitHub URL
* Portfolio URL

Requirements:

* Create appropriate SQLAlchemy models.
* Associate the student profile with the authenticated user.
* Ensure a student can access and update only their own profile.
* Add validation for profile fields.
* Implement REST APIs.
* Use proper HTTP status codes.
* Add tests.

Suggested endpoints:

* `GET /api/students/profile`
* `PUT /api/students/profile`

Do not expose sensitive authentication information through the profile API.

---

# 2. Skills

Create a reusable skill system.

A skill should contain information such as:

* Skill name
* Category
* Description

Examples:

* Python
* Java
* JavaScript
* React
* Flask
* SQL
* PostgreSQL
* Machine Learning
* Data Structures
* Algorithms

Skills should be reusable across students and future job/internship roles.

Requirements:

* Create a `Skill` SQLAlchemy model.
* Prevent accidental duplicate skills.
* Add appropriate relationships.
* Implement skill APIs.
* Validate skill names.
* Support searching/filtering skills where useful.

Suggested endpoints:

* `GET /api/skills`
* `GET /api/skills/<id>`
* `POST /api/skills`

Industry/institution-specific skill creation can be restricted by role if appropriate.

---

# 3. Student Skills

Create the relationship between students and skills.

A student should be able to associate multiple skills with their profile.

The relationship should support information such as:

* Student
* Skill
* Self-assessed proficiency
* Optional years/months of experience
* Source of skill
* Date added/updated

Suggested proficiency levels:

* BEGINNER
* INTERMEDIATE
* ADVANCED
* EXPERT

Requirements:

* Create an appropriate association model.
* Prevent duplicate student-skill relationships.
* Allow students to add skills.
* Allow students to update proficiency.
* Allow students to remove skills.
* Ensure authorization is enforced.

Suggested endpoints:

* `GET /api/students/skills`
* `POST /api/students/skills`
* `PUT /api/students/skills/<skill_id>`
* `DELETE /api/students/skills/<skill_id>`

---

# 4. Projects

Create a project section for student profiles.

A project should support:

* Project title
* Description
* Technologies used
* Project URL
* GitHub URL
* Start date
* End date
* Role/contribution
* Associated skills

Requirements:

* Create SQLAlchemy model.
* Associate projects with students.
* Allow students to create, update, view, and delete their own projects.
* Validate ownership.
* Allow projects to reference skills where appropriate.
* Implement REST APIs.
* Add tests.

Suggested endpoints:

* `GET /api/students/projects`
* `POST /api/students/projects`
* `GET /api/students/projects/<id>`
* `PUT /api/students/projects/<id>`
* `DELETE /api/students/projects/<id>`

---

# 5. Certifications

Create certification management for students.

A certification should support:

* Certification name
* Issuing organization
* Issue date
* Expiry date if applicable
* Credential ID
* Credential URL
* Description

Requirements:

* Associate certifications with students.
* Students can create, update, view, and delete their own certifications.
* Validate ownership.
* Implement REST APIs.
* Add tests.

Suggested endpoints:

* `GET /api/students/certifications`
* `POST /api/students/certifications`
* `GET /api/students/certifications/<id>`
* `PUT /api/students/certifications/<id>`
* `DELETE /api/students/certifications/<id>`

---

# 6. Experience

Create student experience functionality.

Experience should support:

* Organization/company
* Job title
* Employment type
* Location
* Start date
* End date
* Description
* Skills used

Employment types may include:

* INTERNSHIP
* FULL_TIME
* PART_TIME
* FREELANCE
* OTHER

Requirements:

* Associate experience with students.
* Support CRUD operations.
* Validate dates.
* Allow associated skills.
* Enforce ownership.
* Add REST APIs and tests.

Suggested endpoints:

* `GET /api/students/experience`
* `POST /api/students/experience`
* `GET /api/students/experience/<id>`
* `PUT /api/students/experience/<id>`
* `DELETE /api/students/experience/<id>`

---

# 7. Internship History

Track internships separately where useful for placement analytics.

An internship record should support:

* Organization
* Role
* Start date
* End date
* Description
* Skills gained
* Certificate/credential URL
* Internship type
* Status

Requirements:

* Associate internships with students.
* Support CRUD operations.
* Associate relevant skills.
* Enforce ownership.
* Add validation.
* Add tests.

Suggested endpoints:

* `GET /api/students/internships`
* `POST /api/students/internships`
* `GET /api/students/internships/<id>`
* `PUT /api/students/internships/<id>`
* `DELETE /api/students/internships/<id>`

---

# 8. Skill Evidence

Create a system for recording evidence that supports a student's claimed skills.

Evidence can come from:

* Projects
* Certifications
* Internships
* Experience
* Assessments
* Coursework
* Other verified sources

A skill evidence record should support:

* Student
* Skill
* Evidence type
* Evidence title
* Description
* Source/reference URL if available
* Related project/certification/experience/internship where applicable
* Verification status
* Evidence strength if appropriate

Possible evidence types:

* PROJECT
* CERTIFICATION
* INTERNSHIP
* EXPERIENCE
* ASSESSMENT
* COURSEWORK
* OTHER

Possible verification states:

* SELF_REPORTED
* VERIFIED
* PENDING

Important:

Do not implement the final deterministic skill scoring engine in Phase 2.

Phase 3 will handle:

* Proficiency scoring
* Evidence strength
* Semantic relevance
* Skill score
* Skill-gap detection
* Role matching

Phase 2 should only collect and structure the evidence required for those calculations.

---

# 9. Resume Upload & Parsing

Implement basic resume upload functionality.

Supported formats:

* PDF
* DOCX

Recommended libraries:

* PyMuPDF for PDF extraction
* python-docx for DOCX extraction

The system should:

1. Accept a resume upload.
2. Validate file type.
3. Store the uploaded file safely.
4. Extract text.
5. Store the extracted text or appropriate metadata.
6. Associate the resume with the student.
7. Return extraction status.

Suggested endpoint:

`POST /api/students/resume`

Possible response information:

* Upload success
* Filename
* File type
* Extraction status
* Extracted text length
* Resume ID

Do not use Claude AI for resume skill extraction yet.

AI-based extraction and normalization will be implemented in Phase 4A.

Do not claim that AI extraction has been implemented during Phase 2.

---

# 10. Database Design

Use:

**SQLite + SQLAlchemy**

Create appropriate relationships between:

* User
* StudentProfile
* Skill
* StudentSkill
* Project
* Certification
* Experience
* Internship
* SkillEvidence
* Resume

Use foreign keys and relationships properly.

Requirements:

* Avoid unnecessary duplication.
* Add useful indexes where appropriate.
* Add uniqueness constraints where appropriate.
* Use timestamps where useful.
* Preserve existing Phase 1 models and relationships.
* Create/update migrations as necessary.

Do not replace SQLite with PostgreSQL during this phase.

---

# 11. API Design

Keep the existing REST API structure.

Current API areas include:

* `/api/auth`
* `/api/students`
* `/api/skills`
* `/api/assessments`
* `/api/jobs`

Phase 2 primarily works with:

* `/api/students`
* `/api/skills`

Follow consistent:

* JSON request/response format
* HTTP status codes
* Validation
* Error responses
* Authentication
* Authorization

Backend owns the business logic.

---

# 12. Security Requirements

Ensure:

* JWT authentication is required for student-specific endpoints.
* Students can access only their own profile/data.
* User IDs are obtained from the authenticated JWT rather than trusted request-body values.
* File uploads validate allowed extensions/types.
* File paths are sanitized.
* Uploaded files cannot execute as code.
* Secrets are never hardcoded.
* `.env` is not committed.
* Do not expose passwords or password hashes through APIs.

---

# 13. Testing

Add tests for the Phase 2 functionality.

At minimum test:

* Student profile creation/update
* Student profile authorization
* Skill creation/listing
* Student skill creation/update/deletion
* Duplicate student-skill prevention
* Project CRUD
* Certification CRUD
* Experience CRUD
* Internship CRUD
* Skill evidence creation
* Resume upload validation
* Unsupported file types
* Unauthorized requests
* Access to another student's resources

Run the existing Phase 1 tests as well.

Do not break existing authentication tests.

---

# AI / ML Boundary

Claude AI is NOT required for Phase 2.

Do not add AI calls just to make the feature appear intelligent.

Phase 2 is primarily:

**Profile + Skills + Evidence + Resume Data**

Phase 3 will implement deterministic skill intelligence.

Phase 4A will implement Claude integration.

---

# Architecture Decisions

* Backend: Python + Flask
* API: REST
* ORM: SQLAlchemy
* Database: SQLite
* Authentication: JWT
* AI: Claude API
* NLP: Sentence Transformers + cosine similarity
* Resume parsing: PyMuPDF + python-docx
* Frontend: React + Vite
* Charts: Recharts
* Backend owns business logic
* Frontend communicates with backend through REST APIs
* Deterministic scoring is independent of Claude

---

# Folder Structure

Current project:

```text
placement_portal/
├── backend/
│   ├── app/
│   │   ├── models/
│   │   ├── routes/
│   │   ├── schemas/
│   │   ├── services/
│   │   └── utils/
│   ├── migrations/
│   ├── tests/
│   ├── .env.example
│   ├── config.py
│   ├── extensions.py
│   ├── README.md
│   ├── requirements.txt
│   └── run.py
├── database/
├── frontend/
├── ml/
└── progress.md
```

Do not reorganize the entire project unnecessarily.

---

# Important Agent Instructions

1. Read this file completely before making changes.
2. Inspect the existing Phase 1 implementation.
3. Do not recreate or rewrite working Phase 1 code.
4. Do not move to Phase 3.
5. Do not implement Claude AI yet.
6. Do not build the React frontend yet.
7. Do not add fake or placeholder functionality and present it as complete.
8. Reuse existing architecture and conventions.
9. Keep changes focused on Phase 2.
10. Run tests after implementation.
11. Fix errors found during testing.
12. Update this file when Phase 2 progresses.
13. Preserve completed Phase 1 status.
14. Do not delete existing functionality without a clear technical reason.

---

# Current Status

## Phase 1

**Completed and committed.**

## Phase 2

**Completed.**

### Checklist

* [x] Student profile
* [x] Skills
* [x] Student skills
* [x] Projects
* [x] Certifications
* [x] Experience
* [x] Internship history
* [x] Skill evidence
* [x] Resume upload
* [x] Resume text extraction
* [x] Database relationships
* [x] REST APIs
* [x] Validation
* [x] Authorization
* [x] Tests
* [x] Documentation

---

# Known Issues

None currently known.

If an issue is discovered during implementation, document it here instead of silently ignoring it.

---

# Next Task

Complete Phase 2 — Student Profile, Skills & Evidence.

After all Phase 2 checklist items are implemented and tested, stop and report:

1. What was implemented.
2. What tests were run.
3. Whether all tests passed.
4. Any remaining issues.
5. Update this file with the final Phase 2 status.

Do not begin Phase 3 until explicitly instructed.
 
 - - -  
  
 #   P h a s e   2   C o m p l e t i o n   S u m m a r y  
 