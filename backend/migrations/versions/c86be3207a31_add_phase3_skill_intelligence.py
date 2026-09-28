"""Add deterministic assessments and target roles.

Revision ID: c86be3207a31
Revises: b272ba66d420
Create Date: 2026-09-28
"""
from alembic import op
import sqlalchemy as sa

revision = "c86be3207a31"
down_revision = "b272ba66d420"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table("assessments",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("skill_id", sa.Integer(), nullable=False),
        sa.Column("created_by", sa.Integer(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["skill_id"], ["skills.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"))
    op.create_index("ix_assessments_skill_id", "assessments", ["skill_id"])
    op.create_table("assessment_questions",
        sa.Column("id", sa.Integer(), nullable=False), sa.Column("assessment_id", sa.Integer(), nullable=False),
        sa.Column("skill_id", sa.Integer(), nullable=False), sa.Column("prompt", sa.Text(), nullable=False),
        sa.Column("options", sa.JSON(), nullable=False), sa.Column("correct_answer", sa.String(length=500), nullable=False),
        sa.ForeignKeyConstraint(["assessment_id"], ["assessments.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["skill_id"], ["skills.id"], ondelete="RESTRICT"), sa.PrimaryKeyConstraint("id"))
    op.create_index("ix_assessment_questions_assessment_id", "assessment_questions", ["assessment_id"])
    op.create_index("ix_assessment_questions_skill_id", "assessment_questions", ["skill_id"])
    op.create_table("assessment_attempts",
        sa.Column("id", sa.Integer(), nullable=False), sa.Column("assessment_id", sa.Integer(), nullable=False),
        sa.Column("student_id", sa.Integer(), nullable=False), sa.Column("score", sa.Float(), nullable=False),
        sa.Column("correct_answers", sa.Integer(), nullable=False), sa.Column("total_questions", sa.Integer(), nullable=False),
        sa.Column("submitted_at", sa.DateTime(), nullable=False),
        sa.CheckConstraint("score >= 0 AND score <= 100", name="ck_attempt_score_range"),
        sa.ForeignKeyConstraint(["assessment_id"], ["assessments.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["student_id"], ["student_profiles.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"), sa.UniqueConstraint("assessment_id", "student_id", name="uq_assessment_student_attempt"))
    op.create_index("ix_assessment_attempts_assessment_id", "assessment_attempts", ["assessment_id"])
    op.create_index("ix_assessment_attempts_student_id", "assessment_attempts", ["student_id"])
    op.create_table("assessment_answers",
        sa.Column("id", sa.Integer(), nullable=False), sa.Column("attempt_id", sa.Integer(), nullable=False),
        sa.Column("question_id", sa.Integer(), nullable=False), sa.Column("answer", sa.String(length=500), nullable=False),
        sa.Column("is_correct", sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(["attempt_id"], ["assessment_attempts.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["question_id"], ["assessment_questions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"), sa.UniqueConstraint("attempt_id", "question_id", name="uq_attempt_question_answer"))
    op.create_index("ix_assessment_answers_attempt_id", "assessment_answers", ["attempt_id"])
    op.create_table("roles",
        sa.Column("id", sa.Integer(), nullable=False), sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("description", sa.Text(), nullable=True), sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"), sa.UniqueConstraint("name"))
    op.create_table("role_skill_requirements",
        sa.Column("id", sa.Integer(), nullable=False), sa.Column("role_id", sa.Integer(), nullable=False),
        sa.Column("skill_id", sa.Integer(), nullable=False), sa.Column("required_proficiency", sa.Float(), nullable=False),
        sa.Column("weight", sa.Float(), nullable=False),
        sa.CheckConstraint("required_proficiency >= 0 AND required_proficiency <= 100", name="ck_role_required_proficiency"),
        sa.CheckConstraint("weight > 0", name="ck_role_skill_weight"),
        sa.ForeignKeyConstraint(["role_id"], ["roles.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["skill_id"], ["skills.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"), sa.UniqueConstraint("role_id", "skill_id", name="uq_role_required_skill"))
    op.create_index("ix_role_skill_requirements_role_id", "role_skill_requirements", ["role_id"])
    op.create_index("ix_role_skill_requirements_skill_id", "role_skill_requirements", ["skill_id"])


def downgrade():
    op.drop_index("ix_role_skill_requirements_skill_id", table_name="role_skill_requirements")
    op.drop_index("ix_role_skill_requirements_role_id", table_name="role_skill_requirements")
    op.drop_table("role_skill_requirements")
    op.drop_table("roles")
    op.drop_index("ix_assessment_answers_attempt_id", table_name="assessment_answers")
    op.drop_table("assessment_answers")
    op.drop_index("ix_assessment_attempts_student_id", table_name="assessment_attempts")
    op.drop_index("ix_assessment_attempts_assessment_id", table_name="assessment_attempts")
    op.drop_table("assessment_attempts")
    op.drop_index("ix_assessment_questions_skill_id", table_name="assessment_questions")
    op.drop_index("ix_assessment_questions_assessment_id", table_name="assessment_questions")
    op.drop_table("assessment_questions")
    op.drop_index("ix_assessments_skill_id", table_name="assessments")
    op.drop_table("assessments")
