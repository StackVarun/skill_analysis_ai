import { useCallback, useEffect, useMemo, useState } from 'react';
import { api, friendlyError } from '../services/api';

const EMPTY_COMPANY = { name: '', website: '', description: '', location: '' };
const EMPTY_POST = { title: '', description: '', kind: 'JOB', location: '', employment_type: '', eligibility: '', deadline: '', stipend: '', duration: '', required_skills: [] };
const STATUS_LABELS = { APPLIED: 'Applied', REVIEWING: 'Reviewing', SHORTLISTED: 'Shortlisted', INTERVIEW: 'Interview', OFFER: 'Offer', REJECTED: 'Rejected' };
const NEXT_STATUS = { APPLIED: ['REVIEWING', 'SHORTLISTED', 'REJECTED'], REVIEWING: ['SHORTLISTED', 'INTERVIEW', 'REJECTED'], SHORTLISTED: ['INTERVIEW', 'OFFER', 'REJECTED'], INTERVIEW: ['OFFER', 'REJECTED'], OFFER: [], REJECTED: [] };

function Panel({ children, className = '', ...props }) {
  return <section className={`industry-panel ${className}`} {...props}>{children}</section>;
}

function Icon({ children }) {
  return <span className="industry-icon" aria-hidden="true">{children}</span>;
}

function Metric({ label, value, icon, detail }) {
  return <Panel className="industry-metric"><div className="industry-metric-top"><span>{label}</span><Icon>{icon}</Icon></div><strong>{value ?? '—'}</strong><small>{detail}</small></Panel>;
}

function PostingMix({ jobs, internships }) {
  const ready = Number.isFinite(jobs) && Number.isFinite(internships);
  const jobCount = Number.isFinite(jobs) ? jobs : 0;
  const internshipCount = Number.isFinite(internships) ? internships : 0;
  const total = jobCount + internshipCount;
  const jobPercent = total ? Math.round((jobCount / total) * 100) : 0;
  return <Panel className="industry-mix-panel">
    <div className="industry-section-heading"><div><span className="industry-kicker">YOUR PIPELINE</span><h2>Open opportunities</h2></div><span className="industry-total-badge">{total} active</span></div>
    <div className="industry-mix" role="img" aria-label={ready ? `${jobCount} active jobs and ${internshipCount} active internships` : 'Loading open opportunity counts'}>
      <div className="industry-donut" style={{ '--industry-job-share': `${jobPercent}%` }}><div><strong>{ready ? total : '—'}</strong><small>{ready ? 'open' : 'loading'}</small></div></div>
      <div className="industry-legend"><div><i className="job-swatch"/><span>Jobs</span><strong>{ready ? jobCount : '—'}</strong></div><div><i className="internship-swatch"/><span>Internships</span><strong>{ready ? internshipCount : '—'}</strong></div></div>
    </div>
    {!total && <p className="industry-empty-hint">Create your first posting to start attracting candidates.</p>}
  </Panel>;
}

function SkillRequirements({ skills, requiredSkills, setRequiredSkills }) {
  const update = (index, patch) => setRequiredSkills(items => items.map((item, i) => i === index ? { ...item, ...patch } : item));
  return <fieldset className="industry-skill-fieldset"><legend>Required skills <span>Set a proficiency target and importance weight for each skill.</span></legend>
    <div className="industry-requirement-head"><span>Skill</span><span>Target / 100</span><span>Weight</span><span /></div>
    {requiredSkills.map((requirement, index) => <div className="industry-requirement-row" key={`${index}-${requirement.skill_id}`}>
      <select aria-label={`Required skill ${index + 1}`} value={requirement.skill_id} onChange={event => update(index, { skill_id: Number(event.target.value) })} required>
        {skills.map(skill => <option value={skill.id} key={skill.id}>{skill.name}</option>)}
      </select>
      <input aria-label={`${skills.find(skill => skill.id === requirement.skill_id)?.name || 'Skill'} target score`} type="number" min="0" max="100" step="1" value={requirement.required_proficiency} onChange={event => update(index, { required_proficiency: Number(event.target.value) })} required />
      <input aria-label={`${skills.find(skill => skill.id === requirement.skill_id)?.name || 'Skill'} weight`} type="number" min="0.001" max="100" step="0.1" value={requirement.weight} onChange={event => update(index, { weight: Number(event.target.value) })} required />
      <button className="industry-icon-button" type="button" aria-label={`Remove ${skills.find(skill => skill.id === requirement.skill_id)?.name || 'skill'}`} onClick={() => setRequiredSkills(items => items.filter((_, i) => i !== index))}>×</button>
    </div>)}
    <button className="industry-text-button" type="button" disabled={!skills.length || requiredSkills.length >= skills.length} onClick={() => {
      const used = new Set(requiredSkills.map(item => item.skill_id));
      const next = skills.find(skill => !used.has(skill.id));
      if (next) setRequiredSkills(items => [...items, { skill_id: next.id, required_proficiency: 70, weight: 1 }]);
    }}>＋ Add a required skill</button>
    {!requiredSkills.length && <small className="industry-validation">Add at least one required skill to publish.</small>}
  </fieldset>;
}

function ApplicationStatusEditor({ application, onUpdate }) {
  const [next, setNext] = useState(application.status);
  const [saving, setSaving] = useState(false);
  useEffect(() => setNext(application.status), [application.status]);
  const choices = NEXT_STATUS[application.status] || [];
  return <div className="industry-status-editor">
    <select aria-label={`Update status for ${application.student?.full_name || 'applicant'}`} value={next} onChange={event => setNext(event.target.value)}>
      <option value={application.status}>{STATUS_LABELS[application.status] || application.status}</option>
      {choices.map(status => <option value={status} key={status}>{STATUS_LABELS[status]}</option>)}
    </select>
    <button className="industry-text-button" disabled={saving || next === application.status} onClick={async () => { setSaving(true); await onUpdate(application.id, next); setSaving(false); }}>Update</button>
  </div>;
}

function CandidateDetail({ candidate, onClose }) {
  if (!candidate) return null;
  const student = candidate.student || {};
  const match = candidate.match || {};
  const skills = match.required_skills || [];
  const relevantProjects = match.relevant_projects || [];
  const projects = candidate.projects?.length ? candidate.projects : relevantProjects;
  const relevantProjectIds = new Set(relevantProjects.map(project => project.id));
  return <div className="industry-drawer-backdrop" onMouseDown={event => { if (event.target === event.currentTarget) onClose(); }}>
    <aside className="industry-candidate-drawer" aria-label="Candidate details">
      <div className="industry-drawer-top"><span className="industry-kicker">CANDIDATE PROFILE</span><button className="industry-icon-button" aria-label="Close candidate details" onClick={onClose}>×</button></div>
      <div className="industry-candidate-identity"><div className="industry-avatar">{(student.full_name || 'S').trim().slice(0, 1).toUpperCase()}</div><div><h2>{student.full_name || 'Student'}</h2><p>{[student.degree, student.branch].filter(Boolean).join(' · ') || 'Student'}</p></div></div>
      <div className="industry-match-highlight"><div><span>Overall role match</span><small>Based on required skill weights</small></div><strong>{Number.isFinite(match.match_percentage) ? `${match.match_percentage}%` : '—'}</strong></div>
      <div className="industry-detail-section"><h3>Profile</h3><dl className="industry-profile-list">
        {[["Institution", student.institution], ["Graduation", student.graduation_year], ["Location", student.location], ["CGPA", student.cgpa], ["Email", student.email || student.user?.email]].filter(([, value]) => value).map(([label, value]) => <div key={label}><dt>{label}</dt><dd>{value}</dd></div>)}
      </dl><div className="industry-links">{[["LinkedIn", student.linkedin_url], ["GitHub", student.github_url], ["Portfolio", student.portfolio_url]].filter(([, url]) => url).map(([label, url]) => <a key={label} href={url} target="_blank" rel="noreferrer">{label} ↗</a>)}</div></div>
      <div className="industry-detail-section"><h3>Skill profile</h3><div className="industry-candidate-skills">{skills.map(skill => <div className="industry-candidate-skill" key={skill.skill_id}><div><strong>{skill.skill}</strong><span>{skill.student_score} / {skill.required_score}</span></div><div className="industry-score-track"><i style={{ width: `${Math.min(100, Math.max(0, skill.student_score))}%` }} /></div><small>{skill.gap > 0 ? `${skill.gap} point gap` : 'Meets target'}</small></div>)}</div>{match.missing_skills?.length > 0 && <p className="industry-gap-note">Missing skills: {match.missing_skills.join(', ')}</p>}</div>
      <div className="industry-detail-section"><h3>Projects <span className="industry-count-badge">{projects.length}</span></h3>{projects.length ? projects.map(project => <article className="industry-project-item" key={project.id}><div className="industry-project-heading"><strong>{project.title}</strong>{relevantProjectIds.has(project.id) && <span className="industry-relevant-pill">Relevant to this role</span>}</div>{project.description && <p>{project.description}</p>}<div className="industry-links">{project.github_url && <a href={project.github_url} target="_blank" rel="noreferrer">GitHub ↗</a>}{project.project_url && <a href={project.project_url} target="_blank" rel="noreferrer">Project ↗</a>}</div></article>) : <p className="industry-muted">No projects listed.</p>}</div>
      <div className="industry-detail-section"><h3>Certifications <span className="industry-count-badge">{candidate.certifications?.length || 0}</span></h3>{candidate.certifications?.length ? candidate.certifications.map(item => <p className="industry-list-item" key={item.id}><strong>{item.name || item.title}</strong> {item.issuing_organization && <span>· {item.issuing_organization}</span>}</p>) : <p className="industry-muted">No certifications listed.</p>}</div>
      <div className="industry-detail-section"><h3>Relevant experience</h3>{(match.relevant_experience || candidate.experience || []).length ? (match.relevant_experience || candidate.experience).map(item => <p className="industry-list-item" key={item.id}><strong>{item.job_title || item.role || item.organization}</strong>{item.organization && item.job_title && <span> · {item.organization}</span>}</p>) : <p className="industry-muted">No relevant experience listed.</p>}</div>
      <div className="industry-detail-section"><h3>Evidence <span className="industry-count-badge">{match.evidence?.length || 0}</span></h3>{match.evidence?.length ? match.evidence.map(item => <p className="industry-evidence-item" key={item.id}><strong>{item.evidence_title || item.title || item.type}</strong><span>{item.skill_name || skills.find(skill => skill.skill_id === item.skill_id)?.skill} · {(item.verification_status || item.status || 'SELF_REPORTED').replaceAll('_', ' ').toLowerCase()}</span>{item.source_url && <a href={item.source_url} target="_blank" rel="noreferrer">View evidence ↗</a>}</p>) : <p className="industry-muted">No linked evidence for the required skills.</p>}</div>
    </aside>
  </div>;
}

export function IndustryWorkspace() {
  const [summary, setSummary] = useState(null);
  const [company, setCompany] = useState(EMPTY_COMPANY);
  const [opportunities, setOpportunities] = useState([]);
  const [skills, setSkills] = useState([]);
  const [candidates, setCandidates] = useState([]);
  const [candidate, setCandidate] = useState(null);
  const [selectedOpportunity, setSelectedOpportunity] = useState(null);
  const [form, setForm] = useState(EMPTY_POST);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [loadingCandidates, setLoadingCandidates] = useState(false);
  const [error, setError] = useState('');
  const [message, setMessage] = useState('');
  const [query, setQuery] = useState('');
  const [kind, setKind] = useState('ALL');
  const [statusFilter, setStatusFilter] = useState('ALL');

  const refresh = useCallback(async () => {
    setLoading(true);
    setError('');
    const results = await Promise.allSettled([
      api.get('/industry/summary'), api.get('/industry/company'), api.get('/opportunities'), api.get('/skills'),
    ]);
    const failed = results.find(item => item.status === 'rejected');
    if (failed) setError(friendlyError(failed.reason));
    if (results[0].status === 'fulfilled') setSummary(results[0].value || {});
    if (results[1].status === 'fulfilled') setCompany(results[1].value || EMPTY_COMPANY);
    if (results[2].status === 'fulfilled') setOpportunities(Array.isArray(results[2].value) ? results[2].value : []);
    if (results[3].status === 'fulfilled') setSkills(Array.isArray(results[3].value) ? results[3].value : []);
    setLoading(false);
  }, []);

  useEffect(() => { refresh(); }, [refresh]);

  const visibleOpportunities = useMemo(() => opportunities.filter(item => {
    const text = `${item.title} ${item.kind} ${item.location || ''}`.toLowerCase();
    return (kind === 'ALL' || item.kind === kind) && text.includes(query.toLowerCase());
  }), [opportunities, kind, query]);

  async function saveCompany(event) {
    event.preventDefault(); setSaving(true); setError(''); setMessage('');
    try { const saved = await api.put('/industry/company', company); setCompany(saved); setMessage('Company profile saved.'); }
    catch (err) { setError(friendlyError(err)); }
    finally { setSaving(false); }
  }

  async function createOpportunity(event) {
    event.preventDefault(); setSaving(true); setError(''); setMessage('');
    try {
      await api.post('/opportunities', { ...form, deadline: form.deadline || null });
      setForm({ ...EMPTY_POST, required_skills: [] }); setMessage('Opportunity published.');
      await refresh();
    } catch (err) { setError(friendlyError(err)); }
    finally { setSaving(false); }
  }

  async function loadCandidates(opportunity) {
    setSelectedOpportunity(opportunity); setCandidates([]); setStatusFilter('ALL'); setLoadingCandidates(true); setError('');
    try { const result = await api.get(`/opportunities/${opportunity.id}/applications`); setCandidates(Array.isArray(result) ? result : []); }
    catch (err) { setError(friendlyError(err)); }
    finally { setLoadingCandidates(false); }
  }

  async function shortlist(application) {
    setError(''); setMessage('');
    try {
      const updated = await api.post(`/applications/${application.id}/shortlist`, {});
      setCandidates(items => items.map(item => item.id === application.id ? updated : item));
      setCandidate(updated); setMessage(`${application.student?.full_name || 'Candidate'} shortlisted.`);
      await refresh();
    } catch (err) { setError(friendlyError(err)); }
  }

  async function updateStatus(applicationId, status) {
    setError(''); setMessage('');
    try {
      const updated = await api.patch(`/applications/${applicationId}/status`, { status });
      setCandidates(items => items.map(item => item.id === applicationId ? updated : item));
      setCandidate(current => current?.id === applicationId ? updated : current);
      setMessage(`Application moved to ${STATUS_LABELS[status]}.`); await refresh();
    } catch (err) { setError(friendlyError(err)); }
  }

  const filteredCandidates = candidates.filter(item => statusFilter === 'ALL' || item.status === statusFilter);
  const requirements = form.required_skills || [];
  return <div className="industry-workspace">
    <header className="industry-welcome"><div><span className="industry-kicker">INDUSTRY PORTAL</span><h1>Find the right talent</h1><p>Manage opportunities and review candidates against the skills that matter.</p></div><button className="industry-primary-button" onClick={() => document.getElementById('industry-create-opportunity')?.scrollIntoView({ behavior: 'smooth', block: 'start' })}>＋ Post an opportunity</button></header>
    {error && <div className="industry-alert" role="alert"><strong>Something needs attention.</strong> {error}<button aria-label="Dismiss error" onClick={() => setError('')}>×</button></div>}
    {message && <div className="industry-success" role="status">✓ {message}<button aria-label="Dismiss message" onClick={() => setMessage('')}>×</button></div>}

    <div className="industry-metric-grid">
      <Metric label="Active jobs" value={summary?.jobs} icon="↗" detail="Currently accepting applications" />
      <Metric label="Active internships" value={summary?.internships} icon="◇" detail="Intern roles currently open" />
      <Metric label="Applications" value={summary?.applications} icon="▤" detail="Across your opportunities" />
      <Metric label="Shortlisted" value={summary?.shortlisted} icon="☆" detail="Candidates ready for next steps" />
    </div>

    <div className="industry-dashboard-grid">
      <PostingMix jobs={summary?.jobs} internships={summary?.internships} />
      <Panel className="industry-company-panel"><div className="industry-section-heading"><div><span className="industry-kicker">YOUR ORGANIZATION</span><h2>Company profile</h2></div><span className="industry-profile-status">{company.name ? 'Profile ready' : 'Setup needed'}</span></div>
        <form className="industry-company-form" onSubmit={saveCompany}><label>Company name<input required maxLength="200" value={company.name || ''} onChange={event => setCompany({ ...company, name: event.target.value })} placeholder="e.g. Northstar Labs" /></label>
          <div className="industry-form-two"><label>Website<input type="url" maxLength="500" value={company.website || ''} onChange={event => setCompany({ ...company, website: event.target.value })} placeholder="https://company.com" /></label><label>Location<input maxLength="200" value={company.location || ''} onChange={event => setCompany({ ...company, location: event.target.value })} placeholder="City, country" /></label></div>
          <label>About the company<textarea rows="3" value={company.description || ''} onChange={event => setCompany({ ...company, description: event.target.value })} placeholder="What should candidates know about your team?" /></label>
          <button className="industry-secondary-button" disabled={saving}>{saving ? 'Saving…' : 'Save company profile'}</button>
        </form>
      </Panel>
    </div>

    <div className="industry-lower-grid">
      <Panel className="industry-post-form-panel" id="industry-create-opportunity"><div className="industry-section-heading"><div><span className="industry-kicker">GROW YOUR TEAM</span><h2>Post an opportunity</h2><p>Skill weights power the deterministic candidate match.</p></div></div>
        <form className="industry-post-form" onSubmit={createOpportunity}>
          <label>Opportunity type<select value={form.kind} onChange={event => setForm({ ...form, kind: event.target.value })}><option value="JOB">Full-time job</option><option value="INTERNSHIP">Internship</option></select></label>
          <label>Title<input required minLength="2" maxLength="200" value={form.title} onChange={event => setForm({ ...form, title: event.target.value })} placeholder="e.g. Backend Engineer Intern" /></label>
          <label>Description<textarea required minLength="5" rows="4" value={form.description} onChange={event => setForm({ ...form, description: event.target.value })} placeholder="Describe the role, team and responsibilities" /></label>
          <div className="industry-form-two"><label>Location<input maxLength="200" value={form.location} onChange={event => setForm({ ...form, location: event.target.value })} placeholder="Remote or city" /></label><label>Employment type<input maxLength="40" value={form.employment_type} onChange={event => setForm({ ...form, employment_type: event.target.value })} placeholder="Full time, hybrid…" /></label></div>
          <label>Eligibility<input value={form.eligibility} onChange={event => setForm({ ...form, eligibility: event.target.value })} placeholder="Degree, year or other requirements" /></label>
          <div className="industry-form-two"><label>Application deadline<input type="date" value={form.deadline} onChange={event => setForm({ ...form, deadline: event.target.value })} /></label>{form.kind === 'INTERNSHIP' && <label>Stipend<input maxLength="100" value={form.stipend} onChange={event => setForm({ ...form, stipend: event.target.value })} placeholder="Optional" /></label>}</div>
          {form.kind === 'INTERNSHIP' && <label>Duration<input maxLength="100" value={form.duration} onChange={event => setForm({ ...form, duration: event.target.value })} placeholder="e.g. 12 weeks" /></label>}
          <SkillRequirements skills={skills} requiredSkills={requirements} setRequiredSkills={next => setForm(current => ({ ...current, required_skills: typeof next === 'function' ? next(current.required_skills || []) : next }))} />
          <button type="submit" className="industry-primary-button industry-publish-button" disabled={saving || !company.name || !requirements.length}>{saving ? 'Publishing…' : 'Publish opportunity'} <span>→</span></button>
          {!company.name && <small className="industry-validation">Save your company profile before publishing.</small>}
        </form>
      </Panel>

      <Panel className="industry-postings-panel"><div className="industry-section-heading"><div><span className="industry-kicker">HIRING ACTIVITY</span><h2>Your opportunities</h2></div><span className="industry-count-badge">{visibleOpportunities.length}</span></div>
        <div className="industry-post-filters"><input type="search" aria-label="Search opportunities" value={query} onChange={event => setQuery(event.target.value)} placeholder="Search your postings" /><select aria-label="Filter by opportunity type" value={kind} onChange={event => setKind(event.target.value)}><option value="ALL">All types</option><option value="JOB">Jobs</option><option value="INTERNSHIP">Internships</option></select></div>
        {loading ? <p className="industry-empty-state">Loading your workspace…</p> : visibleOpportunities.length ? <div className="industry-opportunity-list">{visibleOpportunities.map(post => <article className={`industry-opportunity-card ${selectedOpportunity?.id === post.id ? 'selected' : ''}`} key={post.id}>
          <div className="industry-opportunity-title"><span className={`industry-kind-pill ${post.kind === 'JOB' ? 'kind-job' : 'kind-internship'}`}>{post.kind === 'JOB' ? 'Job' : 'Internship'}</span><span className={`industry-open-label ${post.is_active ? 'is-open' : 'is-closed'}`}><i />{post.is_active ? 'Active' : 'Closed'}</span></div>
          <h3>{post.title}</h3><p>{post.location || 'Location flexible'}{post.employment_type ? ` · ${post.employment_type}` : ''}</p>
          <div className="industry-post-skill-tags">{(post.required_skills || []).slice(0, 4).map(skill => <span key={skill.skill_id}>{skill.skill}</span>)}{(post.required_skills || []).length > 4 && <span>+{post.required_skills.length - 4}</span>}</div>
          <div className="industry-opportunity-actions"><button className="industry-secondary-button" aria-label={selectedOpportunity?.id === post.id ? 'Refresh applicants' : 'View applicants'} onClick={() => loadCandidates(post)}>{selectedOpportunity?.id === post.id ? 'Refresh applicants' : 'View applicants'} <span aria-hidden="true">→</span></button>{post.is_active && <button className="industry-text-button" onClick={async () => { try { await api.delete(`/opportunities/${post.id}`); await refresh(); setMessage('Opportunity closed.'); } catch (err) { setError(friendlyError(err)); } }}>Close posting</button>}</div>
        </article>)}</div> : <p className="industry-empty-state">{opportunities.length ? 'No postings match your search.' : 'No postings yet. Create your first role to get started.'}</p>}
      </Panel>
    </div>

    <Panel className="industry-applications-panel"><div className="industry-section-heading"><div><span className="industry-kicker">CANDIDATE REVIEW</span><h2>{selectedOpportunity ? `Applicants · ${selectedOpportunity.title}` : 'Applications'}</h2><p>{selectedOpportunity ? 'Review match details, inspect candidate profiles and shortlist.' : 'Choose one of your postings above to review its applicants.'}</p></div>{selectedOpportunity && <button className="industry-text-button" onClick={() => { setSelectedOpportunity(null); setCandidates([]); }}>Clear selection</button>}</div>
      {selectedOpportunity && <><div className="industry-application-toolbar"><span>{candidates.length} applicant{candidates.length === 1 ? '' : 's'}</span><select aria-label="Filter applications by status" value={statusFilter} onChange={event => setStatusFilter(event.target.value)}><option value="ALL">All statuses</option>{Object.entries(STATUS_LABELS).map(([key, label]) => <option value={key} key={key}>{label}</option>)}</select></div>
        {loadingCandidates ? <p className="industry-empty-state">Loading candidate profiles and skill matches…</p> : filteredCandidates.length ? <div className="industry-applicants-list">{filteredCandidates.map(application => {
          const person = application.student || {}; const match = application.match || {};
          const matching = match.matching_skills || (match.required_skills || []).filter(skill => skill.gap === 0);
          const gaps = match.skill_gaps || [];
          return <article className="industry-applicant-row" key={application.id}>
            <div className="industry-applicant-person"><div className="industry-avatar small-avatar">{(person.full_name || 'S').trim().slice(0, 1).toUpperCase()}</div><div><strong>{person.full_name || 'Student'}</strong><small>{[person.degree, person.institution].filter(Boolean).join(' · ') || 'Candidate profile'}</small></div></div>
            <div className="industry-row-match"><strong>{Number.isFinite(match.match_percentage) ? `${match.match_percentage}%` : '—'}</strong><small>role match</small><div className="industry-score-track"><i style={{ width: `${Math.min(100, Math.max(0, match.match_percentage || 0))}%` }} /></div></div>
            <div className="industry-row-skills"><small>Matching skills</small><div>{matching.slice(0, 3).map(skill => <span key={skill.skill_id}>{skill.skill}</span>)}{!matching.length && <em>None yet</em>}</div></div>
            <div className="industry-row-gaps"><small>Skill gaps</small><div>{gaps.slice(0, 2).map(skill => <span key={skill.skill_id}>{skill.skill}</span>)}{!gaps.length && <em>None</em>}</div><small className="industry-evidence-summary">{match.evidence?.length || 0} evidence item{match.evidence?.length === 1 ? '' : 's'}</small></div>
            <div className="industry-row-actions"><span className={`industry-status-pill status-${application.status?.toLowerCase()}`}><strong>{STATUS_LABELS[application.status] || application.status}</strong></span><button className="industry-text-button" onClick={() => setCandidate(application)}>View profile</button>{application.status !== 'SHORTLISTED' && !['OFFER', 'REJECTED'].includes(application.status) && <button className="industry-shortlist-button" onClick={() => shortlist(application)}>☆ Shortlist</button>}</div>
            <div className="industry-row-status"><ApplicationStatusEditor application={application} onUpdate={updateStatus} /></div>
          </article>;
        })}</div> : <p className="industry-empty-state">{candidates.length ? 'No applicants in this status.' : 'No applications have arrived for this posting yet.'}</p>}</>}
    </Panel>
    <CandidateDetail candidate={candidate} onClose={() => setCandidate(null)} />
  </div>;
}
