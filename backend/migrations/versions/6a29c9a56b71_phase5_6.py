"""Industry and faculty opportunities.

Revision ID: 6a29c9a56b71
Revises: c86be3207a31
"""
from alembic import op
import sqlalchemy as sa
revision='6a29c9a56b71'
down_revision='c86be3207a31'
branch_labels=None
depends_on=None

def upgrade():
    op.create_table('institution_profiles',sa.Column('id',sa.Integer,primary_key=True),sa.Column('user_id',sa.Integer,sa.ForeignKey('users.id'),nullable=False,unique=True),sa.Column('name',sa.String(200),nullable=False))
    op.create_table('company_profiles',sa.Column('id',sa.Integer,primary_key=True),sa.Column('user_id',sa.Integer,sa.ForeignKey('users.id'),nullable=False,unique=True),sa.Column('name',sa.String(200),nullable=False),sa.Column('website',sa.String(500)),sa.Column('description',sa.Text),sa.Column('location',sa.String(200)))
    op.create_table('opportunities',sa.Column('id',sa.Integer,primary_key=True),sa.Column('company_id',sa.Integer,sa.ForeignKey('company_profiles.id'),nullable=False),sa.Column('title',sa.String(200),nullable=False),sa.Column('description',sa.Text,nullable=False),sa.Column('kind',sa.String(20),nullable=False),sa.Column('location',sa.String(200)),sa.Column('employment_type',sa.String(40)),sa.Column('eligibility',sa.Text),sa.Column('deadline',sa.Date),sa.Column('stipend',sa.String(100)),sa.Column('duration',sa.String(100)),sa.Column('is_active',sa.Boolean,nullable=False),sa.Column('created_at',sa.DateTime,nullable=False))
    op.create_table('opportunity_skills',sa.Column('opportunity_id',sa.Integer,sa.ForeignKey('opportunities.id'),primary_key=True),sa.Column('skill_id',sa.Integer,sa.ForeignKey('skills.id'),primary_key=True),sa.Column('required_proficiency',sa.Float,nullable=False),sa.Column('weight',sa.Float,nullable=False),sa.CheckConstraint('required_proficiency >= 0 AND required_proficiency <= 100'),sa.CheckConstraint('weight > 0'))
    op.create_table('opportunity_applications',sa.Column('id',sa.Integer,primary_key=True),sa.Column('opportunity_id',sa.Integer,sa.ForeignKey('opportunities.id'),nullable=False),sa.Column('student_id',sa.Integer,sa.ForeignKey('student_profiles.id'),nullable=False),sa.Column('status',sa.String(20),nullable=False),sa.Column('created_at',sa.DateTime,nullable=False),sa.UniqueConstraint('opportunity_id','student_id'))
    op.create_table('faculty_profiles',sa.Column('id',sa.Integer,primary_key=True),sa.Column('user_id',sa.Integer,sa.ForeignKey('users.id'),nullable=False,unique=True),sa.Column('institution',sa.String(200),nullable=False),sa.Column('department',sa.String(200)),sa.Column('designation',sa.String(200)),sa.Column('interests',sa.Text))
    op.create_table('faculty_opportunities',sa.Column('id',sa.Integer,primary_key=True),sa.Column('owner_id',sa.Integer,sa.ForeignKey('users.id'),nullable=False),sa.Column('title',sa.String(200),nullable=False),sa.Column('kind',sa.String(30),nullable=False),sa.Column('description',sa.Text,nullable=False),sa.Column('organization',sa.String(200)),sa.Column('deadline',sa.Date),sa.Column('is_active',sa.Boolean,nullable=False),sa.Column('created_at',sa.DateTime))
    op.create_table('faculty_applications',sa.Column('id',sa.Integer,primary_key=True),sa.Column('opportunity_id',sa.Integer,sa.ForeignKey('faculty_opportunities.id'),nullable=False),sa.Column('applicant_id',sa.Integer,sa.ForeignKey('users.id'),nullable=False),sa.Column('statement',sa.Text,nullable=False),sa.Column('status',sa.String(20),nullable=False),sa.UniqueConstraint('opportunity_id','applicant_id'))

def downgrade():
    for table in ('faculty_applications','faculty_opportunities','faculty_profiles','opportunity_applications','opportunity_skills','opportunities','company_profiles','institution_profiles'):op.drop_table(table)
