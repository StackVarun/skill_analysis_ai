"""Create missing profiles for existing student accounts.

Revision ID: 9d2af314f0c1
Revises: 6a29c9a56b71
"""
from alembic import op
import sqlalchemy as sa


revision = "9d2af314f0c1"
down_revision = "6a29c9a56b71"
branch_labels = None
depends_on = None


def upgrade():
    # User names are the only existing profile data available. Preserve every
    # existing profile and add rows only for student accounts that lack one.
    op.get_bind().execute(sa.text("""
        INSERT INTO student_profiles (user_id, full_name, created_at, updated_at)
        SELECT users.id, trim(users.first_name || ' ' || users.last_name),
               CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
        FROM users
        WHERE users.role = 'STUDENT'
          AND NOT EXISTS (
              SELECT 1 FROM student_profiles
              WHERE student_profiles.user_id = users.id
          )
    """))


def downgrade():
    # Backfilled profile rows may have been edited after upgrade. Keep them.
    pass
