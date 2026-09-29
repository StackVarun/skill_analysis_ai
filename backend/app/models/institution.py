from app.extensions import db
class InstitutionProfile(db.Model):
    __tablename__='institution_profiles'
    id=db.Column(db.Integer,primary_key=True)
    user_id=db.Column(db.Integer,db.ForeignKey('users.id'),unique=True,nullable=False)
    name=db.Column(db.String(200),nullable=False)
