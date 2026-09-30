"""Deterministic scoring, role matching, gaps, and recommendations."""
from flask import current_app
from app.extensions import db
from app.models.assessment import Assessment, AssessmentQuestion, AssessmentAttempt, AssessmentAnswer
from app.models.role import Role, RoleSkillRequirement
from app.models.skill import Skill
from app.models.student_skill import StudentSkill, ProficiencyLevel
from app.models.skill_evidence import SkillEvidence, EvidenceType, VerificationStatus
from app.models.project import Project
from app.models.experience import Experience
from app.models.internship import Internship

LEVEL_SCORES = {ProficiencyLevel.BEGINNER: 25, ProficiencyLevel.INTERMEDIATE: 50, ProficiencyLevel.ADVANCED: 75, ProficiencyLevel.EXPERT: 100}
RECOMMENDATION_TOPICS = {
    "python": ["Python fundamentals", "Functions, collections, and exception handling"],
    "sql": ["SQL joins", "Aggregation and subqueries"],
    "dsa": ["Arrays and hashing", "Linked lists and trees"],
    "flask": ["Flask routing", "REST APIs and authentication"],
    "docker": ["Containers and images", "Dockerfiles and compose"],
}
DEFAULT_TOPICS = ["Review core concepts", "Build a small practical project", "Practice skill-specific exercises"]


class SkillIntelligenceService:
    @staticmethod
    def create_assessment(title, skill_id, description=None, questions=None, created_by=None):
        skill = Skill.query.get(skill_id)
        if not skill:
            raise ValueError("Skill not found")
        assessment = Assessment(title=title.strip(), description=description, skill_id=skill_id, created_by=created_by)
        for q in questions or []:
            if q["skill_id"] != skill_id and not Skill.query.get(q["skill_id"]):
                raise ValueError("Question skill not found")
            if q["skill_id"] != skill_id:
                raise ValueError("Question skill must match assessment skill")
            assessment.questions.append(AssessmentQuestion(skill_id=q["skill_id"], prompt=q["prompt"], options=q["options"], correct_answer=q["correct_answer"]))
        db.session.add(assessment)
        db.session.commit()
        return assessment

    @staticmethod
    def serialize_assessment(assessment, include_answers=False):
        return {"id": assessment.id, "title": assessment.title, "description": assessment.description,
                "skill": {"id": assessment.skill.id, "name": assessment.skill.name}, "is_active": assessment.is_active,
                "questions": [{"id": q.id, "skill_id": q.skill_id, "prompt": q.prompt, "options": q.options,
                               **({"correct_answer": q.correct_answer} if include_answers else {})} for q in assessment.questions]}

    @staticmethod
    def submit_assessment(assessment_id, student_id, answers):
        assessment = Assessment.query.filter_by(id=assessment_id, is_active=True).first()
        if not assessment:
            raise LookupError("Assessment not found")
        if not assessment.questions:
            raise ValueError("Assessment has no questions")
        if AssessmentAttempt.query.filter_by(assessment_id=assessment_id, student_id=student_id).first():
            raise ValueError("Assessment has already been submitted")
        expected = {q.id: q for q in assessment.questions}
        submitted = {item["question_id"]: item["answer"] for item in answers}
        if len(submitted) != len(answers) or set(submitted) != set(expected):
            raise ValueError("Submit exactly one valid answer for every question")
        for qid, answer in submitted.items():
            if answer not in (expected[qid].options or []):
                raise ValueError("Answer must be one of the question options")
        correct = sum(submitted[qid] == q.correct_answer for qid, q in expected.items())
        score = round(correct / len(expected) * 100, 2)
        attempt = AssessmentAttempt(assessment_id=assessment_id, student_id=student_id, score=score, correct_answers=correct, total_questions=len(expected))
        for qid, answer in submitted.items():
            attempt.answers.append(AssessmentAnswer(question_id=qid, answer=answer, is_correct=answer == expected[qid].correct_answer))
        db.session.add(attempt)
        db.session.flush()
        from app.services.faculty_support_service import queue_review
        queue_review(student_id, "ASSESSMENT", attempt.id)
        db.session.commit()
        return attempt

    @staticmethod
    def serialize_attempt(attempt):
        return {"id": attempt.id, "assessment_id": attempt.assessment_id, "score": attempt.score,
                "correct_answers": attempt.correct_answers, "total_questions": attempt.total_questions,
                "submitted_at": attempt.submitted_at.isoformat(), "answers": [{"question_id": a.question_id, "answer": a.answer, "is_correct": a.is_correct} for a in attempt.answers]}

    @staticmethod
    def student_scores(student_id):
        skills = {s.skill_id: s for s in StudentSkill.query.filter_by(student_id=student_id).all()}
        attempts = AssessmentAttempt.query.join(Assessment).filter(AssessmentAttempt.student_id == student_id).all()
        assessment_scores = {}
        for attempt in attempts:
            assessment_scores.setdefault(attempt.assessment.skill_id, []).append(attempt.score)
        skill_ids = set(skills) | set(assessment_scores) | {e.skill_id for e in SkillEvidence.query.filter_by(student_id=student_id).all()}
        for entity in (Project, Experience, Internship):
            skill_ids.update(skill.id for record in entity.query.filter_by(student_id=student_id).all() for skill in record.skills)
        result = []
        for skill_id in skill_ids:
            skill = Skill.query.get(skill_id)
            if not skill:
                continue
            proficiency = SkillIntelligenceService.proficiency_score(skills.get(skill_id), assessment_scores.get(skill_id, []))
            evidence = SkillIntelligenceService.evidence_score(student_id, skill_id)
            proficiency_weight = current_app.config.get("SKILL_PROFICIENCY_WEIGHT", 0.60)
            evidence_weight = current_app.config.get("SKILL_EVIDENCE_WEIGHT", 0.40)
            if proficiency_weight < 0 or evidence_weight < 0 or proficiency_weight + evidence_weight <= 0:
                raise ValueError("Skill score weights must be non-negative and have a positive sum")
            total = proficiency_weight + evidence_weight
            overall = round((proficiency_weight * proficiency + evidence_weight * evidence) / total, 2)
            result.append({"skill_id": skill_id, "skill": skill.name, "proficiency_score": proficiency, "evidence_score": evidence, "overall_score": overall})
        return sorted(result, key=lambda row: row["skill"].lower())

    @staticmethod
    def proficiency_score(student_skill, assessment_scores):
        self_score = LEVEL_SCORES.get(student_skill.proficiency, 0) if student_skill else None
        if assessment_scores and self_score is not None:
            return round(0.7 * (sum(assessment_scores) / len(assessment_scores)) + 0.3 * self_score, 2)
        if assessment_scores:
            return round(sum(assessment_scores) / len(assessment_scores), 2)
        return float(self_score or 0)

    @staticmethod
    def evidence_score(student_id, skill_id):
        items = SkillEvidence.query.filter_by(student_id=student_id, skill_id=skill_id).all()
        total = 0.0
        represented = {"PROJECT": set(), "EXPERIENCE": set(), "INTERNSHIP": set()}
        for item in items:
            kind = item.evidence_type if isinstance(item.evidence_type, EvidenceType) else EvidenceType(item.evidence_type)
            status = item.verification_status if isinstance(item.verification_status, VerificationStatus) else VerificationStatus(item.verification_status)
            strength = min(1.0, max(0.0, item.evidence_strength if item.evidence_strength is not None else 1.0))
            weights = current_app.config.get("SKILL_EVIDENCE_TYPE_WEIGHTS", {})
            weight = weights.get(kind.value, 0)
            verified = current_app.config.get("SKILL_EVIDENCE_VERIFIED_MULTIPLIER", 1.2)
            total += weight * strength * (verified if status == VerificationStatus.VERIFIED else 1)
            if item.project_id: represented["PROJECT"].add(item.project_id)
            if item.experience_id: represented["EXPERIENCE"].add(item.experience_id)
            if item.internship_id: represented["INTERNSHIP"].add(item.internship_id)
        # Phase 2 project, experience, and internship skill associations are
        # evidence on their own; avoid counting an explicitly linked record twice.
        for kind, entity in (("PROJECT", Project), ("EXPERIENCE", Experience), ("INTERNSHIP", Internship)):
            records = entity.query.filter_by(student_id=student_id).join(entity.skills).filter(Skill.id == skill_id).all()
            direct_count = sum(record.id not in represented[kind] for record in records)
            total += direct_count * current_app.config.get("SKILL_EVIDENCE_TYPE_WEIGHTS", {}).get(kind, 0)
        return round(min(100.0, total), 2)

    @staticmethod
    def analyze_role(student_id, role):
        scores = {item["skill_id"]: item["overall_score"] for item in SkillIntelligenceService.student_scores(student_id)}
        rows = []
        for requirement in role.requirements:
            current = scores.get(requirement.skill_id, 0)
            missing = requirement.skill_id not in scores or current == 0
            gap = max(0, round(requirement.required_proficiency - current, 2))
            minor_max = current_app.config.get("SKILL_GAP_MINOR_MAX", 10)
            moderate_max = current_app.config.get("SKILL_GAP_MODERATE_MAX", 25)
            category = "meets_requirement" if gap == 0 else "minor" if gap <= minor_max else "moderate" if gap <= moderate_max else "major"
            contribution = round(current * requirement.weight, 2)
            rows.append({"skill_id": requirement.skill_id, "skill": requirement.skill.name, "student_score": current,
                         "required_score": requirement.required_proficiency, "gap": gap, "gap_category": category,
                         "missing": missing, "weight": requirement.weight, "contribution": contribution})
        total_weight = sum(row["weight"] for row in rows)
        match = round(sum(row["student_score"] * row["weight"] for row in rows) / total_weight, 2) if total_weight else 0
        return {"role_id": role.id, "role": role.name, "match_percentage": match, "required_skills": rows,
                "missing_skills": [row["skill"] for row in rows if row["missing"]], "skill_gaps": [row for row in rows if row["gap"] > 0]}

    @staticmethod
    def recommendations(student_id, role_id=None):
        if role_id:
            role = Role.query.get(role_id)
            if not role:
                raise LookupError("Role not found")
            gaps = SkillIntelligenceService.analyze_role(student_id, role)["skill_gaps"]
        else:
            scores = {r["skill_id"]: r["overall_score"] for r in SkillIntelligenceService.student_scores(student_id)}
            gaps = [{"skill_id": req.skill_id, "skill": req.skill.name, "student_score": scores.get(req.skill_id, 0), "required_score": req.required_proficiency, "gap": max(0, req.required_proficiency - scores.get(req.skill_id, 0)), "missing": req.skill_id not in scores or not scores.get(req.skill_id)} for role in Role.query.all() for req in role.requirements]
            by_id = {}
            for gap in gaps:
                if gap["gap"] > by_id.get(gap["skill_id"], {}).get("gap", 0): by_id[gap["skill_id"]] = gap
            gaps = list(by_id.values())
        output = []
        for gap in gaps:
            if gap["gap"] <= 0: continue
            name = gap["skill"].lower()
            priority = "high" if gap["missing"] or gap["gap"] > 25 else "medium" if gap["gap"] > 10 else "low"
            output.append({"skill_id": gap["skill_id"], "skill": gap["skill"], "current_score": gap["student_score"], "required_score": gap["required_score"], "gap": gap["gap"], "priority": priority, "recommended_topics": next((topics for key, topics in RECOMMENDATION_TOPICS.items() if key in name), DEFAULT_TOPICS)})
        return sorted(output, key=lambda row: ({"high": 0, "medium": 1, "low": 2}[row["priority"]], -row["gap"], row["skill"].lower()))

    @staticmethod
    def seed_roles():
        from app.services.reference_data_service import ReferenceDataService
        return ReferenceDataService.seed()["roles"]
