"""Aggregated institution reporting and private student skill passport."""
from collections import Counter, defaultdict
from flask import Blueprint, jsonify
from sqlalchemy import func
from flask_jwt_extended import get_current_user
from app.utils.decorators import roles_required
from app.models.student_profile import StudentProfile
from app.models.opportunity import Opportunity, OpportunityApplication
from app.models.role import Role
from app.models.assessment import AssessmentAttempt
from app.models.skill import Skill
from app.models.institution import InstitutionProfile
from app.services.skill_intelligence_service import SkillIntelligenceService as Engine
from app.services.opportunity_service import is_open, match_candidate

institution_bp=Blueprint('institution',__name__)

def passport(student):
    scores=Engine.student_scores(student.id)
    roles=[Engine.analyze_role(student.id,r) for r in Role.query.all()]
    roles.sort(key=lambda r:r['match_percentage'],reverse=True)
    openings=[{'opportunity':p.to_dict(),'match':match_candidate(p,student)} for p in Opportunity.query.all() if is_open(p)]
    openings.sort(key=lambda r:r['match']['match_percentage'],reverse=True)
    return {'student':student.to_dict(),'skills':scores,
            'projects':[p.to_dict() for p in student.projects],
            'certifications':[c.to_dict() for c in student.certifications],
            'experience':[e.to_dict() for e in student.experiences],
            'internships':[i.to_dict() for i in student.internships],
            'assessments':[{'title':a.assessment.title,'score':a.score,'submitted_at':a.submitted_at.isoformat()} for a in student.assessment_attempts],
            'role_readiness':roles,'opportunities':openings[:5]}

@institution_bp.get('/passport/me')
@roles_required('STUDENT')
def my_passport():
    student=StudentProfile.query.filter_by(user_id=get_current_user().id).first()
    if not student:return jsonify({'error':'Student profile required'}),404
    return jsonify(passport(student))

@institution_bp.get('/institution/analytics')
@roles_required('INSTITUTION')
def analytics():
    # Institution administrators see aggregate data only for their named institution.
    profile=InstitutionProfile.query.filter_by(user_id=get_current_user().id).first()
    if not profile:return jsonify({'error':'Institution account is not configured'}),403
    institution=profile.name
    students=StudentProfile.query.filter(func.lower(StudentProfile.institution) == institution.lower()).all()
    ids={s.id for s in students}
    scores={s.id:Engine.student_scores(s.id) for s in students}
    role_rows=[Engine.analyze_role(s.id,r) for s in students for r in Role.query.all()]
    gaps=Counter(row['skill'] for result in role_rows for row in result['skill_gaps'])
    demand=defaultdict(float)
    for post in Opportunity.query.all():
        if not is_open(post):continue
        for r in post.requirements:demand[r.skill.name]+=r.weight
    apps=OpportunityApplication.query.all()
    participation=sum(a.student_id in ids and a.opportunity.kind=='INTERNSHIP' for a in apps)
    readiness=round(sum(r['match_percentage'] for r in role_rows)/len(role_rows),2) if role_rows else 0
    return jsonify({'institution':institution,'student_count':len(students),
                    'placement_readiness':readiness,'internship_applications':participation,
                    'common_skill_gaps':[{'skill':name,'count':count} for name,count in gaps.most_common(10)],
                    'skill_demand':[{'skill':name,'weight':weight} for name,weight in sorted(demand.items(),key=lambda row:-row[1])[:10]],
                    'average_skill_scores':[{'skill':name,'score':round(sum(values)/len(values),2)} for name,values in sorted(_group_scores(scores).items())]})

def _group_scores(scores):
    grouped=defaultdict(list)
    for rows in scores.values():
        for row in rows:grouped[row['skill']].append(row['overall_score'])
    return grouped
