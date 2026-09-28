"""Deterministic skill assessments and student attempts."""
from datetime import datetime, timezone
from app.extensions import db


class Assessment(db.Model):
    __tablename__ = "assessments"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    skill_id = db.Column(db.Integer, db.ForeignKey("skills.id", ondelete="RESTRICT"), nullable=False, index=True)
    created_by = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    skill = db.relationship("Skill")
    questions = db.relationship("AssessmentQuestion", back_populates="assessment", cascade="all, delete-orphan", order_by="AssessmentQuestion.id")
    attempts = db.relationship("AssessmentAttempt", back_populates="assessment", cascade="all, delete-orphan")


class AssessmentQuestion(db.Model):
    __tablename__ = "assessment_questions"
    id = db.Column(db.Integer, primary_key=True)
    assessment_id = db.Column(db.Integer, db.ForeignKey("assessments.id", ondelete="CASCADE"), nullable=False, index=True)
    skill_id = db.Column(db.Integer, db.ForeignKey("skills.id", ondelete="RESTRICT"), nullable=False, index=True)
    prompt = db.Column(db.Text, nullable=False)
    options = db.Column(db.JSON, nullable=False)
    correct_answer = db.Column(db.String(500), nullable=False)
    assessment = db.relationship("Assessment", back_populates="questions")
    skill = db.relationship("Skill")


class AssessmentAttempt(db.Model):
    __tablename__ = "assessment_attempts"
    id = db.Column(db.Integer, primary_key=True)
    assessment_id = db.Column(db.Integer, db.ForeignKey("assessments.id", ondelete="CASCADE"), nullable=False, index=True)
    student_id = db.Column(db.Integer, db.ForeignKey("student_profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    score = db.Column(db.Float, nullable=False)
    correct_answers = db.Column(db.Integer, nullable=False)
    total_questions = db.Column(db.Integer, nullable=False)
    submitted_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    assessment = db.relationship("Assessment", back_populates="attempts")
    student = db.relationship("StudentProfile", backref=db.backref("assessment_attempts", cascade="all, delete-orphan"))
    answers = db.relationship("AssessmentAnswer", back_populates="attempt", cascade="all, delete-orphan")
    __table_args__ = (db.UniqueConstraint("assessment_id", "student_id", name="uq_assessment_student_attempt"), db.CheckConstraint("score >= 0 AND score <= 100", name="ck_attempt_score_range"))


class AssessmentAnswer(db.Model):
    __tablename__ = "assessment_answers"
    id = db.Column(db.Integer, primary_key=True)
    attempt_id = db.Column(db.Integer, db.ForeignKey("assessment_attempts.id", ondelete="CASCADE"), nullable=False, index=True)
    question_id = db.Column(db.Integer, db.ForeignKey("assessment_questions.id", ondelete="CASCADE"), nullable=False)
    answer = db.Column(db.String(500), nullable=False)
    is_correct = db.Column(db.Boolean, nullable=False)
    attempt = db.relationship("AssessmentAttempt", back_populates="answers")
    question = db.relationship("AssessmentQuestion")
    __table_args__ = (db.UniqueConstraint("attempt_id", "question_id", name="uq_attempt_question_answer"),)
