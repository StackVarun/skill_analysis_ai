"""Candidate matching uses the existing deterministic Phase 3 engine."""
from datetime import date
from app.models.role import Role, RoleSkillRequirement
from app.models.skill_evidence import SkillEvidence
from app.services.skill_intelligence_service import SkillIntelligenceService

def is_open(post):
    return post.is_active and (not post.deadline or post.deadline >= date.today())

def match_candidate(post, student):
    role = Role(name=post.title)
    role.requirements = [RoleSkillRequirement(skill_id=r.skill_id,required_proficiency=r.required_proficiency,weight=r.weight) for r in post.requirements]
    for req, posted in zip(role.requirements,post.requirements): req.skill = posted.skill
    result = SkillIntelligenceService.analyze_role(student.id,role)
    ids = {r.skill_id for r in post.requirements}
    result['evidence'] = [{'skill_id':e.skill_id,'type':e.evidence_type.value,'status':e.verification_status.value} for e in SkillEvidence.query.filter_by(student_id=student.id).all() if e.skill_id in ids]
    result['relevant_projects'] = [p.to_dict() for p in student.projects if any(s.id in ids for s in p.skills)]
    return result

def candidate_record(application):
    student = application.student
    return {**application.to_dict(),'student':student.to_dict(),
            'projects':[p.to_dict() for p in student.projects],
            'certifications':[c.to_dict() for c in student.certifications],
            'experience':[e.to_dict() for e in student.experiences],
            'match':match_candidate(application.opportunity,student)}
