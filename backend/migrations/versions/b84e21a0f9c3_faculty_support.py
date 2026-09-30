"""Add project completion, faculty review queues and mentorship tasks.

Revision ID: b84e21a0f9c3
Revises: 9d2af314f0c1
"""
from alembic import op
import sqlalchemy as sa

revision = 'b84e21a0f9c3'
down_revision = '9d2af314f0c1'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('projects', sa.Column('completion_status', sa.String(20), nullable=False, server_default='COMPLETED'))
    op.create_table('verification_requests',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('student_id', sa.Integer(), sa.ForeignKey('student_profiles.id', ondelete='CASCADE'), nullable=False),
        sa.Column('kind', sa.String(20), nullable=False),
        sa.Column('project_id', sa.Integer(), sa.ForeignKey('projects.id', ondelete='CASCADE'), unique=True),
        sa.Column('attempt_id', sa.Integer(), sa.ForeignKey('assessment_attempts.id', ondelete='CASCADE'), unique=True),
        sa.Column('evidence_id', sa.Integer(), sa.ForeignKey('skill_evidence.id', ondelete='CASCADE'), unique=True),
        sa.Column('status', sa.String(25), nullable=False),
        sa.Column('version', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('reviewer_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='SET NULL')),
        sa.Column('feedback', sa.Text()),
        sa.Column('student_response', sa.Text()),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('reviewed_at', sa.DateTime()),
        sa.CheckConstraint("status IN ('PENDING','APPROVED','CHANGES_REQUESTED','WITHDRAWN')", name='ck_review_status'),
        sa.CheckConstraint("(kind = 'PROJECT' AND project_id IS NOT NULL AND attempt_id IS NULL AND evidence_id IS NULL) OR (kind = 'ASSESSMENT' AND attempt_id IS NOT NULL AND project_id IS NULL AND evidence_id IS NULL) OR (kind = 'EVIDENCE' AND evidence_id IS NOT NULL AND project_id IS NULL AND attempt_id IS NULL)", name='ck_review_source'))
    op.create_index('ix_verification_requests_student_id', 'verification_requests', ['student_id'])
    op.create_table('mentorship_tasks',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('faculty_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('student_id', sa.Integer(), sa.ForeignKey('student_profiles.id', ondelete='CASCADE'), nullable=False),
        sa.Column('skill_id', sa.Integer(), sa.ForeignKey('skills.id', ondelete='SET NULL')),
        sa.Column('project_id', sa.Integer(), sa.ForeignKey('projects.id', ondelete='SET NULL')),
        sa.Column('role_id', sa.Integer(), sa.ForeignKey('roles.id', ondelete='SET NULL')),
        sa.Column('kind', sa.String(25), nullable=False),
        sa.Column('title', sa.String(200), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('due_date', sa.Date()),
        sa.Column('status', sa.String(20), nullable=False),
        sa.Column('submission', sa.Text()),
        sa.Column('feedback', sa.Text()),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.CheckConstraint("kind IN ('COURSEWORK','RESEARCH','PROJECT_SUPERVISION')", name='ck_mentorship_kind'),
        sa.CheckConstraint("status IN ('ASSIGNED','IN_PROGRESS','SUBMITTED','COMPLETED')", name='ck_mentorship_status'))
    op.create_index('ix_mentorship_tasks_student_id', 'mentorship_tasks', ['student_id'])
    op.create_index('ix_mentorship_tasks_faculty_id', 'mentorship_tasks', ['faculty_id'])
    # Existing portfolios/assessment submissions also appear in the faculty inbox.
    bind = op.get_bind()
    for table, kind, column in [('projects', 'PROJECT', 'project_id'), ('assessment_attempts', 'ASSESSMENT', 'attempt_id'), ('skill_evidence', 'EVIDENCE', 'evidence_id')]:
        bind.execute(sa.text(f"INSERT INTO verification_requests (student_id, kind, {column}, status, created_at, updated_at) SELECT student_id, :kind, id, 'PENDING', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP FROM {table}"), {'kind': kind})


def downgrade():
    op.drop_table('mentorship_tasks')
    op.drop_table('verification_requests')
    with op.batch_alter_table('projects') as batch:
        batch.drop_column('completion_status')
