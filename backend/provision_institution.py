"""Provision an institution administrator locally using environment variables.

INSTITUTION_EMAIL=... INSTITUTION_PASSWORD=... INSTITUTION_NAME=... python provision_institution.py
"""
import os
from app import create_app
from app.extensions import db
from app.models.user import User
from app.models.institution import InstitutionProfile

email=os.environ.get('INSTITUTION_EMAIL','').strip().lower()
password=os.environ.get('INSTITUTION_PASSWORD','')
name=os.environ.get('INSTITUTION_NAME','').strip()
if not email or len(password)<8 or not name:
    raise SystemExit('Set INSTITUTION_EMAIL, INSTITUTION_PASSWORD (8+ chars), and INSTITUTION_NAME')
with create_app().app_context():
    if User.query.filter_by(email=email).first():raise SystemExit('Email already exists')
    user=User(email=email,password=password,first_name='Institution',last_name='Admin',role='INSTITUTION')
    db.session.add(user);db.session.flush()
    db.session.add(InstitutionProfile(user_id=user.id,name=name))
    db.session.commit()
    print(f'Provisioned institution: {name}')
