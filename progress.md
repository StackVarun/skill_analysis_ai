# Phase 3 â€” Skill Intelligence Engine

## Objective

Build a deterministic Skill Intelligence Engine using only:

* Python
* Flask
* SQLAlchemy
* SQLite
* Existing Phase 2 student data

No AI models or external AI APIs are required.

The system should convert student data into:

**Assessment â†’ Proficiency â†’ Evidence â†’ Skill Score â†’ Skill Gaps â†’ Role Matching â†’ Recommendations**

---

## 1. Skill Assessment

Implement:

* Assessment
* Assessment questions
* Student attempts
* Student answers
* Assessment results
* Skill-wise scores

Assessment scoring must be deterministic.

Normalize scores to a 0â€“100 range.

Example:

```text
Correct answers / Total questions Ã— 100
```

---

## 2. Proficiency Score

Create a centralized proficiency calculation service.

Use existing StudentSkill data and assessment results.

Keep the calculation deterministic and explainable.

Do not use AI or ML.

---

## 3. Evidence Score

Use existing:

* Projects
* Certifications
* Experience
* Internships
* Skill Evidence
* Resume-derived structured information where available

Assign configurable weights to evidence types.

Example:

```text
Project       â†’ 25
Certification â†’ 20
Experience    â†’ 30
Internship    â†’ 30
Verified evidence â†’ additional weight where appropriate
```

Keep all weights centralized.

Do not invent evidence.

---

## 4. Overall Skill Score

Calculate an overall skill score from structured information.

Initial formula:

```text
60% Ã— Proficiency
40% Ã— Evidence Strength
```

Keep the weights configurable.

Return:

```json
{
  "skill": "Python",
  "proficiency_score": 80,
  "evidence_score": 70,
  "overall_score": 76
}
```

All calculations must be deterministic.

---

## 5. Target Roles

Create a role system.

A role should contain:

* Role name
* Description
* Required skills
* Skill weights
* Minimum required proficiency

Examples:

```text
Backend Developer
Software Engineer
Frontend Developer
Data Analyst
Data Scientist
```

Do not hardcode role logic inside Flask routes.

---

## 6. Role Matching

Calculate role compatibility using the student's existing skill scores.

Example:

```text
Python       â†’ 80
SQL          â†’ 70
Flask        â†’ 85
Docker       â†’ 40
```

For each role, compare the student's skill score against the required skill score.

Use a deterministic weighted formula.

Example:

```text
Role Match =
Î£(student_skill_score Ã— skill_weight)
---------------------------------------
Î£(skill_weight)
```

Return the contributing skills and scores.

Do not use AI or ML.

---

## 7. Skill Gap Detection

For the selected target role:

```text
Required Score - Student Score = Gap
```

Example:

```text
SQL:
Required = 75
Student = 55
Gap = 20
```

Classify gaps:

```text
0       â†’ Meets requirement
1â€“10    â†’ Minor gap
11â€“25   â†’ Moderate gap
26+     â†’ Major gap
```

The thresholds should be configurable.

Also identify completely missing required skills.

---

## 8. Learning Recommendations

Create a rule-based recommendation system.

No AI.

No ML.

No external API.

Recommendations should be generated from skill gaps.

Example:

```text
Python gap
â†’ Python fundamentals

SQL gap
â†’ SQL joins, aggregation, subqueries

DSA gap
â†’ Arrays, hashing, linked lists, trees

Flask gap
â†’ Flask routing, REST APIs, authentication

Docker gap
â†’ Containers, images, Dockerfiles
```

Store recommendation data in structured configuration or database tables rather than putting large rules inside routes.

---

## 9. REST APIs

Expose the Phase 3 functionality through the existing Flask REST architecture.

Suggested endpoints:

```text
/api/assessments
/api/skills/scores
/api/skill-gaps
/api/roles
/api/role-matches
/api/recommendations
```

Follow the existing:

* JWT authentication
* Authorization
* Marshmallow validation
* Service layer
* Error handling
* HTTP status conventions

---

## 10. Database

Create only the models required for Phase 3.

Possible models:

* Assessment
* AssessmentQuestion
* AssessmentAttempt
* AssessmentAnswer
* Role
* RoleSkillRequirement
* LearningRecommendation

Reuse all existing Phase 2 models.

Do not duplicate:

* StudentProfile
* Skill
* StudentSkill
* Project
* Certification
* Experience
* Internship
* SkillEvidence
* Resume

Create migrations for new models.

---

## 11. Architecture

Maintain:

```text
Routes
   â†“
Schemas
   â†“
Services
   â†“
Business Logic
   â†“
Models / Database
```

Keep scoring and matching logic inside dedicated services.

Do not put business logic directly in route functions.

---

## 12. Testing

Create tests for:

* Assessment creation
* Assessment submission
* Assessment scoring
* Proficiency calculation
* Evidence scoring
* Overall skill score
* Role creation
* Role requirements
* Role matching
* Skill gap detection
* Missing skills
* Recommendations
* Authorization
* Validation
* Boundary scores
* Empty data
* Invalid data

Run the complete existing test suite as regression testing.

Phase 1 and Phase 2 functionality must continue passing.

---

## 13. No AI / ML Requirement

This project intentionally does NOT use:

* Claude
* OpenAI
* Gemini
* Sentence Transformers
* Hugging Face models
* Embeddings
* Machine-learning models
* External AI APIs
* Paid APIs

The intelligence layer is implemented using:

* deterministic formulas
* weighted scoring
* configurable thresholds
* database-driven rules
* rule-based recommendations

The system must remain fully functional without an AI model or external AI service.

---

## Phase 3 Checklist

* [x] Assessment model
* [x] Assessment questions
* [x] Assessment attempts
* [x] Assessment answers
* [x] Assessment scoring
* [x] Proficiency scoring
* [x] Evidence scoring
* [x] Overall skill score
* [x] Role model
* [x] Role skill requirements
* [x] Role matching
* [x] Skill gap detection
* [x] Rule-based recommendations
* [x] REST APIs
* [x] Validation
* [x] Authorization
* [x] Database migrations
* [x] Unit tests
* [x] API tests
* [x] Full regression tests
* [x] Documentation

---

## Current Status

### Phase 1

Completed and committed.

### Phase 2

Completed and committed.

### Phase 3

Implemented and regression tested. See `backend/README.md` for formulas and API behavior.

---

## Phase 4A â€” Free/Local AI Backend

### Objective

Add a free/local AI backend layer for generative tasks that benefit from natural-language reasoning.

The AI layer must operate **on top of the deterministic Phase 3 Skill Intelligence Engine**.

The AI layer must NOT replace or modify deterministic Phase 3 calculations.

### AI-supported features

* [x] Resume skill extraction
* [x] Skill normalization suggestions
* [x] Skill-gap explanations
* [x] Personalized learning roadmap generation

### Deterministic Phase 3 responsibilities remain unchanged

The AI layer must NOT calculate:

* [ ] Skill scores
* [ ] Proficiency scores
* [ ] Evidence scores
* [ ] Semantic similarity
* [ ] Role-match percentages
* [ ] Numerical skill gaps
* [ ] Assessment scores

These remain handled by the Phase 3 deterministic services.

### Free/Local AI Backend

* [x] Local AI service abstraction
* [x] Local model/runtime integration
* [x] No paid external AI API
* [x] No API key requirement
* [x] Request timeout handling
* [x] Model/runtime error handling
* [x] Safe structured response parsing
* [x] AI response validation
* [x] Graceful fallback when local AI is unavailable
* [x] AI model configuration kept separate from routes

### APIs

* [x] Resume skill extraction API
* [x] Skill normalization API
* [x] Skill-gap explanation API
* [x] Personalized roadmap API

### Testing

* [x] Successful AI response
* [x] Mocked AI response
* [x] Malformed response handling
* [x] Timeout handling
* [x] Model/runtime failure handling
* [x] Missing model/runtime handling
* [x] Fallback behavior
* [x] Authentication/authorization
* [x] Phase 3 regression tests

### Requirements

The application must remain fully functional without the local AI model.

Phase 3 deterministic functionality must continue working even when the AI runtime or model is unavailable.

No Claude, Anthropic, OpenAI, Gemini, or other paid external AI API is required.

### Phase 4A implementation notes

The architecture is `AI routes â†’ LocalAIService â†’ OllamaAdapter â†’ loopback Ollama runtime`. The adapter uses Python's standard library HTTP client, and Flask does not load a model at startup. The default local model is `qwen2.5:1.5b-instruct-q5_0`; install Ollama and run `ollama run qwen2.5:1.5b-instruct-q5_0` to enable local generation. Runtime URL, model name, timeout, and input limit are environment-configurable in `backend/config.py` and listed in `backend/.env.example`.

All four APIs are authenticated and student-scoped. Resume skills are catalog-matched suggestions with source evidence, are labeled unverified, and are never persisted by AI. Normalization must match an existing skill. Gap explanations and roadmaps receive Phase 3 results; their numeric scores, role match, and gaps are carried through unchanged. When the local runtime is unavailable or its output times out, is empty, malformed, or fails validation, the service returns a labeled deterministic fallback. Tests replace the adapter with mocked responses and do not download a model.

### Current Status

Implemented and regression tested with an optional local Ollama runtime and Qwen2.5 1.5B instruct model. The backend starts and Phase 3 remains available without Ollama or downloaded models. See `backend/README.md` for setup, APIs, configuration, and fallback behavior.

## Phase 4B â€” Frontend & Student Dashboard

### Objective

Build the frontend interface for SkillBridge AI and connect it to the existing backend APIs from Phases 1â€“4A.

The frontend should present the student's profile, skills, assessments, skill scores, skill gaps, role matching, recommendations, and AI-powered insights through a clear and responsive dashboard.

The frontend must consume existing backend APIs rather than duplicating business logic.

### Core Frontend

* [x] Frontend project setup
* [x] Responsive application layout
* [x] Navigation/sidebar
* [x] Authentication pages
* [x] Login
* [x] Registration
* [x] Protected routes
* [x] Student dashboard
* [x] Profile page
* [x] Skills page
* [x] Projects page
* [x] Certifications page
* [x] Experience/internships page

### Skill Intelligence Dashboard

* [x] Overall skill score visualization
* [x] Individual skill scores
* [x] Proficiency scores
* [x] Evidence scores
* [x] Assessment interface
* [x] Assessment results
* [x] Skill-gap visualization
* [x] Missing required skills
* [x] Role matching results
* [x] Target-role selection
* [x] Rule-based learning recommendations

### AI Features

Consume the Phase 4A APIs for:

* [x] Resume skill extraction
* [x] Skill normalization suggestions
* [x] Skill-gap explanations
* [x] Personalized learning roadmap

AI-generated information must be clearly distinguishable from verified/deterministic student data.

The frontend must not calculate:

* [ ] Skill scores
* [ ] Proficiency scores
* [ ] Evidence scores
* [ ] Skill gaps
* [ ] Role-match percentages

All numerical intelligence must come from the backend.

### API Integration

* [x] Centralized API client
* [x] JWT authentication handling
* [x] Authenticated API requests
* [x] Loading states
* [x] Empty states
* [x] Validation errors
* [x] API error handling
* [x] AI unavailable/fallback states
* [x] Session/logout handling

### UX & Accessibility

* [x] Responsive design
* [x] Clear visual hierarchy
* [x] Accessible buttons and forms
* [x] Keyboard-friendly navigation
* [x] Form validation
* [x] Appropriate loading indicators
* [x] User-friendly error messages

### Testing

* [x] Frontend component tests
* [x] Authentication flow testing
* [x] API integration testing
* [x] Protected-route testing
* [x] Assessment flow testing
* [x] Dashboard data rendering
* [x] Skill-gap rendering
* [x] AI fallback-state testing
* [x] Responsive layout testing (tablet/mobile breakpoint regression coverage)

### Requirements

The frontend must work with the existing Flask backend.

Do not move backend business logic into the frontend.

Do not duplicate Phase 3 scoring or matching formulas in frontend code.

Do not expose local AI runtime configuration or model details unnecessarily to users.

### Current Status

Phase 4B frontend is implemented. The frontend test suite passes (9 tests), and the Vite production build succeeds. Responsive tablet/mobile breakpoints have regression coverage. See `frontend/README.md` for setup and test commands.

Do not begin Phase 5 or industry-specific features until explicitly instructed.\n
## Phase 5A / 5B / 6 — integration (2026-09-29)

- Added company profile, industry job/internship postings, skills and weights, student applications and tracking, candidate match details, ownership checks, shortlist actions, and industry dashboard.
- Candidate matching reuses Phase 3 `analyze_role`; no second numeric scoring algorithm.
- Added faculty profile, opportunity types, faculty applications and owner shortlisting; institution aggregate analytics scoped to a provisioned institution; student digital skill passport.
- Added role-aware React screens, migration, demo seed, and setup instructions.
- Verification: full backend suite, frontend tests and production build, migration on clean SQLite database. See root README for demo flow and limitations.
