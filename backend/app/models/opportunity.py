from datetime import datetime, timezone
from app.extensions import db

APPLICATION_STATUSES = ('APPLIED', 'REVIEWING', 'SHORTLISTED', 'INTERVIEW', 'OFFER', 'REJECTED')
APPLICATION_TRANSITIONS = {
    'APPLIED': ('REVIEWING', 'SHORTLISTED', 'REJECTED'),
    'REVIEWING': ('SHORTLISTED', 'INTERVIEW', 'REJECTED'),
    'SHORTLISTED': ('INTERVIEW', 'OFFER', 'REJECTED'),
    'INTERVIEW': ('OFFER', 'REJECTED'),
    'OFFER': (),
    'REJECTED': (),
}

class CompanyProfile(db.Model):
    __tablename__ = 'company_profiles'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), unique=True, nullable=False)
    name = db.Column(db.String(200), nullable=False)
    website = db.Column(db.String(500))
    description = db.Column(db.Text)
    location = db.Column(db.String(200))
    def to_dict(self):
        return {key: getattr(self, key) for key in ('id','user_id','name','website','description','location')}

class Opportunity(db.Model):
    __tablename__ = 'opportunities'
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('company_profiles.id'), nullable=False, index=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    kind = db.Column(db.String(20), nullable=False)
    location = db.Column(db.String(200))
    employment_type = db.Column(db.String(40))
    eligibility = db.Column(db.Text)
    deadline = db.Column(db.Date)
    stipend = db.Column(db.String(100))
    duration = db.Column(db.String(100))
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    company = db.relationship('CompanyProfile')
    requirements = db.relationship('OpportunitySkill', back_populates='opportunity', cascade='all, delete-orphan')
    applications = db.relationship('OpportunityApplication', back_populates='opportunity', cascade='all, delete-orphan')
    def to_dict(self):
        return {'id':self.id,'company':self.company.to_dict(),'title':self.title,'description':self.description,
                'kind':self.kind,'location':self.location,'employment_type':self.employment_type,
                'eligibility':self.eligibility,'deadline':self.deadline.isoformat() if self.deadline else None,
                'stipend':self.stipend,'duration':self.duration,'is_active':self.is_active,
                'required_skills':[{'skill_id':r.skill_id,'skill':r.skill.name,
                'required_proficiency':r.required_proficiency,'weight':r.weight} for r in self.requirements]}

class OpportunitySkill(db.Model):
    __tablename__ = 'opportunity_skills'
    opportunity_id = db.Column(db.Integer, db.ForeignKey('opportunities.id'), primary_key=True)
    skill_id = db.Column(db.Integer, db.ForeignKey('skills.id'), primary_key=True)
    required_proficiency = db.Column(db.Float, nullable=False)
    weight = db.Column(db.Float, nullable=False)
    opportunity = db.relationship('Opportunity', back_populates='requirements')
    skill = db.relationship('Skill')
    __table_args__ = (db.CheckConstraint('required_proficiency >= 0 AND required_proficiency <= 100'),db.CheckConstraint('weight > 0'))

class OpportunityApplication(db.Model):
    __tablename__ = 'opportunity_applications'
    id = db.Column(db.Integer, primary_key=True)
    opportunity_id = db.Column(db.Integer, db.ForeignKey('opportunities.id'), nullable=False, index=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student_profiles.id'), nullable=False, index=True)
    status = db.Column(db.String(20), default='APPLIED', nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    opportunity = db.relationship('Opportunity', back_populates='applications')
    student = db.relationship('StudentProfile')
    __table_args__ = (db.UniqueConstraint('opportunity_id','student_id'),)
    def to_dict(self):
        return {'id':self.id,'opportunity_id':self.opportunity_id,'student_id':self.student_id,
                'status':self.status,'created_at':self.created_at.isoformat()}
