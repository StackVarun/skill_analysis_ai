from datetime import datetime, timezone
from app.extensions import db

class FacultyProfile(db.Model):
    __tablename__ = 'faculty_profiles'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), unique=True, nullable=False)
    institution = db.Column(db.String(200), nullable=False)
    department = db.Column(db.String(200))
    designation = db.Column(db.String(200))
    interests = db.Column(db.Text)
    def to_dict(self):return {k:getattr(self,k) for k in ('id','user_id','institution','department','designation','interests')}

class FacultyOpportunity(db.Model):
    __tablename__ = 'faculty_opportunities'
    id = db.Column(db.Integer, primary_key=True)
    owner_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    title = db.Column(db.String(200),nullable=False)
    kind = db.Column(db.String(30),nullable=False)
    description = db.Column(db.Text,nullable=False)
    organization = db.Column(db.String(200))
    deadline = db.Column(db.Date)
    is_active = db.Column(db.Boolean,default=True,nullable=False)
    created_at = db.Column(db.DateTime,default=lambda:datetime.now(timezone.utc))
    applications = db.relationship('FacultyApplication',back_populates='opportunity',cascade='all, delete-orphan')
    def to_dict(self):
        return {'id':self.id,'owner_id':self.owner_id,'title':self.title,'kind':self.kind,
                'description':self.description,'organization':self.organization,
                'deadline':self.deadline.isoformat() if self.deadline else None,'is_active':self.is_active}

class FacultyApplication(db.Model):
    __tablename__ = 'faculty_applications'
    id = db.Column(db.Integer,primary_key=True)
    opportunity_id = db.Column(db.Integer,db.ForeignKey('faculty_opportunities.id'),nullable=False)
    applicant_id = db.Column(db.Integer,db.ForeignKey('users.id'),nullable=False)
    statement = db.Column(db.Text,nullable=False)
    status = db.Column(db.String(20),default='APPLIED',nullable=False)
    opportunity = db.relationship('FacultyOpportunity',back_populates='applications')
    __table_args__ = (db.UniqueConstraint('opportunity_id','applicant_id'),)
    def to_dict(self):return {'id':self.id,'opportunity_id':self.opportunity_id,'applicant_id':self.applicant_id,'statement':self.statement,'status':self.status}
