"""Faculty endorsement and targeted student support records."""
from datetime import datetime, timezone
from app.extensions import db


def now():
    return datetime.now(timezone.utc)


class VerificationRequest(db.Model):
    __tablename__ = 'verification_requests'
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student_profiles.id', ondelete='CASCADE'), nullable=False, index=True)
    kind = db.Column(db.String(20), nullable=False)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id', ondelete='CASCADE'), unique=True)
    attempt_id = db.Column(db.Integer, db.ForeignKey('assessment_attempts.id', ondelete='CASCADE'), unique=True)
    evidence_id = db.Column(db.Integer, db.ForeignKey('skill_evidence.id', ondelete='CASCADE'), unique=True)
    status = db.Column(db.String(25), nullable=False, default='PENDING')
    version = db.Column(db.Integer, nullable=False, default=1, server_default='1')
    reviewer_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'))
    feedback = db.Column(db.Text)
    student_response = db.Column(db.Text)
    created_at = db.Column(db.DateTime, nullable=False, default=now)
    updated_at = db.Column(db.DateTime, nullable=False, default=now, onupdate=now)
    reviewed_at = db.Column(db.DateTime)
    student = db.relationship('StudentProfile', backref=db.backref('verification_requests', cascade='all, delete-orphan'))
    project = db.relationship('Project', backref=db.backref('verification_request', uselist=False, cascade='all, delete-orphan'))
    attempt = db.relationship('AssessmentAttempt', backref=db.backref('verification_request', uselist=False, cascade='all, delete-orphan'))
    evidence = db.relationship('SkillEvidence', backref=db.backref('verification_request', uselist=False, cascade='all, delete-orphan'))
    reviewer = db.relationship('User')
    __table_args__ = (
        db.CheckConstraint("status IN ('PENDING','APPROVED','CHANGES_REQUESTED','WITHDRAWN')", name='ck_review_status'),
        db.CheckConstraint("(kind = 'PROJECT' AND project_id IS NOT NULL AND attempt_id IS NULL AND evidence_id IS NULL) OR (kind = 'ASSESSMENT' AND attempt_id IS NOT NULL AND project_id IS NULL AND evidence_id IS NULL) OR (kind = 'EVIDENCE' AND evidence_id IS NOT NULL AND project_id IS NULL AND attempt_id IS NULL)", name='ck_review_source'),
    )
    def to_dict(self):
        title = self.project.title if self.project else self.attempt.assessment.title if self.attempt else self.evidence.evidence_title if self.evidence else 'Removed item'
        return dict(id=self.id, student_id=self.student_id, student={**self.student.to_dict(), 'email': self.student.user.email}, kind=self.kind,
                    title=title, project_id=self.project_id, attempt_id=self.attempt_id, evidence_id=self.evidence_id,
                    status=self.status, version=self.version, feedback=self.feedback, student_response=self.student_response, reviewer=self.reviewer.full_name if self.reviewer else None,
                    reviewed_at=self.reviewed_at.isoformat() if self.reviewed_at else None,
                    updated_at=self.updated_at.isoformat() if self.updated_at else None,
                    project=self.project.to_dict() if self.project else None,
                    assessment=dict(title=self.attempt.assessment.title, skill=self.attempt.assessment.skill.name,
                                    skill_id=self.attempt.assessment.skill_id, score=self.attempt.score,
                                    correct_answers=self.attempt.correct_answers, total_questions=self.attempt.total_questions) if self.attempt else None,
                    evidence=self.evidence.to_dict() if self.evidence else None)


class MentorshipTask(db.Model):
    __tablename__ = 'mentorship_tasks'
    id = db.Column(db.Integer, primary_key=True)
    faculty_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student_profiles.id', ondelete='CASCADE'), nullable=False, index=True)
    skill_id = db.Column(db.Integer, db.ForeignKey('skills.id', ondelete='SET NULL'))
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id', ondelete='SET NULL'))
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id', ondelete='SET NULL'))
    kind = db.Column(db.String(25), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    due_date = db.Column(db.Date)
    status = db.Column(db.String(20), nullable=False, default='ASSIGNED')
    submission = db.Column(db.Text)
    feedback = db.Column(db.Text)
    created_at = db.Column(db.DateTime, nullable=False, default=now)
    updated_at = db.Column(db.DateTime, nullable=False, default=now, onupdate=now)
    student = db.relationship('StudentProfile', backref=db.backref('mentorship_tasks', cascade='all, delete-orphan'))
    faculty = db.relationship('User', backref=db.backref('assigned_mentorship_tasks', cascade='all, delete-orphan'))
    skill = db.relationship('Skill')
    project = db.relationship('Project', backref='supervision_tasks')
    role = db.relationship('Role')
    __table_args__ = (
        db.CheckConstraint("kind IN ('COURSEWORK','RESEARCH','PROJECT_SUPERVISION')", name='ck_mentorship_kind'),
        db.CheckConstraint("status IN ('ASSIGNED','IN_PROGRESS','SUBMITTED','COMPLETED')", name='ck_mentorship_status'),
    )
    def to_dict(self):
        return dict(id=self.id, faculty_id=self.faculty_id, faculty_name=self.faculty.full_name,
                    student_id=self.student_id, student_name=self.student.full_name,
                    skill_id=self.skill_id, skill=self.skill.name if self.skill else None,
                    project_id=self.project_id, project=self.project.title if self.project else None,
                    role_id=self.role_id, kind=self.kind, title=self.title, description=self.description,
                    due_date=self.due_date.isoformat() if self.due_date else None, status=self.status,
                    submission=self.submission, feedback=self.feedback)
