import { useCallback, useEffect, useMemo, useState } from 'react';
import { useOutletContext } from 'react-router-dom';
import { api, friendlyError } from '../services/api';
import { useAuth } from '../context/AuthContext';
import { useResource } from '../hooks/useResource';
import { EmptyState, ErrorNotice, Loading, Notice } from '../components/Feedback';
import ProgressBar from '../components/ProgressBar';

const PROFICIENCY = ['BEGINNER', 'INTERMEDIATE', 'ADVANCED', 'EXPERT'];
const noop = async () => [];
const paths = {
  projects: '/students/projects', certifications: '/students/certifications',
  experience: '/students/experience', internships: '/students/internships',
};

function useSelectedRole() {
  const context = useOutletContext();
  return context || { targetRoleId: '', setTargetRoleId: () => {} };
}

function SectionHeading({ eyebrow, title, description, action }) {
  return <div className="section-heading"><div><span className="eyebrow">{eyebrow}</span><h2>{title}</h2>{description && <p>{description}</p>}</div>{action}</div>;
}

function TargetRolePicker({ roles, value, onChange }) {
  return <label className="compact-select">Target role<select aria-label="Target role" value={value || ''} onChange={(event) => onChange(event.target.value)}><option value="">Choose a role</option>{roles.map((role) => <option key={role.id} value={role.id}>{role.name}</option>)}</select></label>;
}

function useRoleData() {
  const loader = useCallback(async () => {
    const roles = await api.get('/roles');
    const results = await Promise.all(roles.map(async (role) => {
      try { return await api.get(`/roles/${role.id}/match`); }
      catch { return null; }
    }));
    return { roles, matches: results.filter(Boolean) };
  }, []);
  return useResource(loader, [loader]);
}

export function DashboardPage() {
  const { user } = useAuth();
  const { targetRoleId, setTargetRoleId } = useSelectedRole();
  const load = useCallback(async () => {
    const safe = async (path, fallback) => { try { return await api.get(path); } catch { return fallback; } };
    const [profile, studentSkills, scores, roles, assessments, evidence, projects] = await Promise.all([
      safe('/students/profile', null), safe('/students/skills', []), safe('/skills/scores', []),
      safe('/roles', []), safe('/assessments', []), safe('/students/skill-evidence', []), safe('/students/projects', []),
    ]);
    const matches = (await Promise.all(roles.map((role) => safe(`/roles/${role.id}/match`, null)))).filter(Boolean);
    const details = (await Promise.all(assessments.map((item) => safe(`/assessments/${item.id}`, null)))).filter(Boolean);
    const chosen = roles.find((role) => String(role.id) === String(targetRoleId)) || roles[0] || null;
    const targetAnalysis = chosen ? await safe(`/skill-gaps?role_id=${chosen.id}`, null) : null;
    const recommendations = chosen ? await safe(`/recommendations?role_id=${chosen.id}`, []) : [];
    return { profile, studentSkills, scores, roles, assessments: details, evidence, projects, matches, chosen, targetAnalysis, recommendations };
  }, [targetRoleId]);
  const { data, loading, error, refresh } = useResource(load, [load]);
  useEffect(() => {
    if (data?.chosen && String(data.chosen.id) !== String(targetRoleId)) setTargetRoleId(String(data.chosen.id));
  }, [data?.chosen?.id, targetRoleId, setTargetRoleId]);
  if (loading) return <Loading />;
  if (!data) return <ErrorNotice onRetry={refresh}>{error}</ErrorNotice>;
  const scores = data.scores || [];
  const topScore = [...scores].sort((a, b) => b.overall_score - a.overall_score)[0];
  const attempted = (data.assessments || []).filter((assessment) => assessment.result).sort((a, b) => (b.result.submitted_at || '').localeCompare(a.result.submitted_at || ''));
  const topRoles = [...data.matches].sort((a, b) => b.match_percentage - a.match_percentage).slice(0, 3);
  const profileReady = Boolean(data.profile?.full_name || data.profile?.institution || data.profile?.degree);
  return <div className="page-stack">
    {!profileReady && <Notice><strong>Set up your profile to get started.</strong> Add your education details so your workspace is ready to use. <a href="/app/profile">Complete profile →</a></Notice>}
    <section className="welcome-panel"><div className="welcome-copy"><span className="eyebrow light-eyebrow">YOUR PROGRESS, IN ONE PLACE</span><h2>Good {greeting()}, {data.profile?.full_name?.split(' ')[0] || user?.first_name || 'there'}.</h2><p>Build on your strengths and find a clear next step toward the roles you want.</p><div className="welcome-actions"><a className="button button-white" href="/app/skills">Explore my skills <span>→</span></a><a className="welcome-link" href="/app/roles">View role matches</a></div></div><div className="welcome-art" aria-hidden="true"><div className="welcome-circle circle-back"/><div className="welcome-circle circle-front"><span>✦</span><small>YOUR NEXT<br/>OPPORTUNITY</small></div><div className="art-spark spark-a">✧</div><div className="art-spark spark-b">✦</div></div></section>
    <div className="stat-grid">
      <StatCard icon="✳" tint="lavender" label="Skills tracked" value={data.studentSkills.length} note={topScore ? `Top score · ${topScore.skill}` : 'Add a skill to get started'} />
      <StatCard icon="↗" tint="mint" label="Highest skill score" value={topScore ? `${topScore.overall_score}%` : '—'} note="Overall score from Phase 3" />
      <StatCard icon="⌁" tint="peach" label="Open skill gaps" value={data.targetAnalysis?.skill_gaps?.length ?? '—'} note={data.chosen ? `For ${data.chosen.name}` : 'Select a target role'} />
      <StatCard icon="◈" tint="blue" label="Roles matched" value={data.matches.filter((item) => item.match_percentage > 0).length} note="Based on your current skills" />
    </div>
    <div className="dashboard-grid">
      <section className="surface-card role-card"><div className="card-heading"><div><span className="eyebrow">CAREER DIRECTION</span><h3>Role matches</h3></div><a className="subtle-link" href="/app/roles">Explore roles <span>→</span></a></div>
        {topRoles.length ? <div className="top-role-list">{topRoles.map((item, index) => <div className="top-role-row" key={item.role_id}><span className={`rank-badge rank-${index + 1}`}>{String(index + 1).padStart(2, '0')}</span><div className="role-row-main"><strong>{item.role}</strong><small>{item.skill_gaps?.length || 0} skills to strengthen</small></div><div className="role-match-value">{item.match_percentage}<small>% match</small></div></div>)}</div> : <EmptyState icon="◈" title="No role matches yet">Role match data will appear once roles are available.</EmptyState>}
      </section>
      <section className="surface-card target-card"><div className="card-heading"><div><span className="eyebrow">YOUR TARGET</span><h3>{data.chosen?.name || 'Choose a role'}</h3></div><span className="target-icon">◎</span></div>
        <TargetRolePicker roles={data.roles} value={data.chosen?.id || ''} onChange={setTargetRoleId} />
        {data.targetAnalysis ? <><div className="target-score-row"><span>Role match</span><strong>{data.targetAnalysis.match_percentage}<small>%</small></strong></div><ProgressBar score={data.targetAnalysis.match_percentage} /><p className="supporting-copy">{data.targetAnalysis.missing_skills?.length || 0} missing skills · {data.targetAnalysis.skill_gaps?.length || 0} development areas</p></> : <p className="supporting-copy">Choose a role to see your current match and skill gaps.</p>}
      </section>
      <section className="surface-card assessment-card"><div className="card-heading"><div><span className="eyebrow">KEEP LEARNING</span><h3>Recent assessments</h3></div><a className="subtle-link" href="/app/assessments">All assessments <span>→</span></a></div>
        {attempted.length ? attempted.slice(0, 3).map((item) => <div className="assessment-row" key={item.id}><span className="assessment-mini">✓</span><div><strong>{item.title}</strong><small>{item.skill.name} · {new Date(item.result.submitted_at).toLocaleDateString()}</small></div><b>{item.result.score}%</b></div>) : <EmptyState icon="▤" title="Your first assessment awaits">Try a skill assessment to start building a progress history.</EmptyState>}
      </section>
      <section className="surface-card action-card"><div className="card-heading"><div><span className="eyebrow">GOOD NEXT STEPS</span><h3>Learning actions</h3></div><span className="action-star">✧</span></div>
        {data.recommendations?.length ? data.recommendations.slice(0, 3).map((item) => <a className="action-row" href="/app/recommendations" key={item.skill_id}><span className="action-check">↗</span><span><strong>Build {item.skill}</strong><small>{item.recommended_topics?.[0]}</small></span><span className={`priority priority-${item.priority}`}>{item.priority}</span></a>) : <div className="action-placeholder"><p>Choose a target role to get learning actions based on your skill gaps.</p><a href="/app/recommendations">See recommendations →</a></div>}
      </section>
    </div>
    <footer className="page-foot"><span>SkillBridge Student Workspace</span><span>Scores and role insights are provided by the backend.</span></footer>
  </div>;
}

function greeting() { const hour = new Date().getHours(); return hour < 12 ? 'morning' : hour < 18 ? 'afternoon' : 'evening'; }
function StatCard({ icon, tint, label, value, note }) { return <article className="stat-card"><span className={`stat-icon ${tint}`}>{icon}</span><div className="stat-label">{label}</div><div className="stat-value">{value}</div><div className="stat-note">{note}</div></article>; }

const EMPTY_PROFILE = { full_name: '', phone: '', institution: '', degree: '', branch: '', graduation_year: '', cgpa: '', bio: '', location: '', linkedin_url: '', github_url: '', portfolio_url: '' };
const PROFILE_FIELDS = [
  ['full_name', 'Full name', 'text'], ['phone', 'Phone number', 'tel'], ['institution', 'Institution', 'text'],
  ['degree', 'Degree', 'text'], ['branch', 'Branch or specialization', 'text'], ['graduation_year', 'Graduation year', 'number'],
  ['cgpa', 'CGPA (out of 10)', 'number'], ['location', 'Location', 'text'], ['linkedin_url', 'LinkedIn URL', 'url'],
  ['github_url', 'GitHub URL', 'url'], ['portfolio_url', 'Portfolio URL', 'url'],
];

export function ProfilePage() {
  const { user } = useAuth();
  const load = useCallback(async () => { try { return await api.get('/students/profile'); } catch (error) { if (error.status === 404) return null; throw error; } }, []);
  const { data, loading, error, refresh } = useResource(load, [load]);
  const [form, setForm] = useState(EMPTY_PROFILE);
  const [notice, setNotice] = useState(''); const [failure, setFailure] = useState(''); const [busy, setBusy] = useState(false);
  useEffect(() => { if (data) setForm({ ...EMPTY_PROFILE, ...data }); }, [data]);
  async function save(event) {
    event.preventDefault(); setBusy(true); setNotice(''); setFailure('');
    const payload = { ...form, graduation_year: form.graduation_year ? Number(form.graduation_year) : null, cgpa: form.cgpa ? Number(form.cgpa) : null };
    Object.keys(payload).forEach((key) => { if (payload[key] === '') payload[key] = null; });
    try { await api.put('/students/profile', payload); setNotice('Your profile has been saved.'); await refresh(); }
    catch (reason) { setFailure(friendlyError(reason)); } finally { setBusy(false); }
  }
  if (loading) return <Loading />;
  return <div className="page-stack"><SectionHeading eyebrow="YOUR FOUNDATION" title="Student profile" description="Keep your education and contact details up to date. This profile is private to your student account." />
    <ErrorNotice onRetry={refresh}>{error}</ErrorNotice>{notice && <Notice tone="success">{notice}</Notice>}{failure && <ErrorNotice>{failure}</ErrorNotice>}
    <div className="profile-layout"><aside className="surface-card profile-card"><div className="profile-avatar">{(form.full_name || user?.full_name || 'S').slice(0, 1).toUpperCase()}</div><h3>{form.full_name || user?.full_name || 'Your name'}</h3><p>{user?.email}</p><span className="profile-tag">STUDENT</span><div className="profile-divider"/><div className="profile-detail"><small>INSTITUTION</small><strong>{form.institution || 'Add your institution'}</strong></div><div className="profile-detail"><small>PROGRAM</small><strong>{[form.degree, form.branch].filter(Boolean).join(' · ') || 'Add your degree'}</strong></div></aside>
    <form className="surface-card profile-form" onSubmit={save}><div className="card-heading"><div><span className="eyebrow">PROFILE DETAILS</span><h3>About you</h3></div><span className="form-lock">◉ Private</span></div><div className="form-grid">{PROFILE_FIELDS.map(([name, label, type]) => <label className={name === 'full_name' || name === 'bio' ? 'span-two' : ''} key={name}>{label}<input name={name} type={type} value={form[name] ?? ''} onChange={(event) => setForm({ ...form, [name]: event.target.value })} min={type === 'number' && name === 'cgpa' ? 0 : undefined} max={type === 'number' && name === 'cgpa' ? 10 : undefined} /></label>)}<label className="span-two">Short introduction<textarea rows="4" name="bio" value={form.bio || ''} onChange={(event) => setForm({ ...form, bio: event.target.value })} placeholder="What are you studying, building, or interested in?" /></label></div><div className="form-footer"><span>Your profile information is only used to personalize your workspace.</span><button className="button button-primary" disabled={busy}>{busy ? 'Saving…' : 'Save profile'} <span>→</span></button></div></form></div>
  </div>;
}

export function SkillsPage() {
  const load = useCallback(async () => {
    const [skills, scores, evidence, catalog] = await Promise.all([api.get('/students/skills'), api.get('/skills/scores'), api.get('/students/skill-evidence'), api.get('/skills')]);
    return { skills, scores, evidence, catalog };
  }, []);
  const { data, loading, error, refresh } = useResource(load, [load]);
  const [selected, setSelected] = useState(''); const [level, setLevel] = useState('BEGINNER'); const [busy, setBusy] = useState(false); const [failure, setFailure] = useState(''); const [notice, setNotice] = useState('');
  async function addSkill(event) { event.preventDefault(); setBusy(true); setFailure(''); setNotice(''); try { await api.post('/students/skills', { skill_id: Number(selected), proficiency: level }); setSelected(''); setNotice('Skill added to your profile.'); await refresh(); } catch (reason) { setFailure(friendlyError(reason)); } finally { setBusy(false); } }
  async function removeSkill(id) { if (!window.confirm('Remove this skill from your profile?')) return; try { await api.delete(`/students/skills/${id}`); await refresh(); } catch (reason) { setFailure(friendlyError(reason)); } }
  if (loading) return <Loading />;
  const scores = new Map((data?.scores || []).map((item) => [item.skill_id, item]));
  const mine = data?.skills || [];
  const skillIds = new Set(mine.map((skill) => skill.skill_id));
  const available = (data?.catalog || []).filter((skill) => !skillIds.has(skill.id));
  return <div className="page-stack"><SectionHeading eyebrow="YOUR CAPABILITIES" title="Skills & evidence" description="See the skill strengths calculated by the backend and the evidence supporting your profile." action={<span className="data-source-pill">✳ Backend scores</span>} />
    <ErrorNotice onRetry={refresh}>{error}</ErrorNotice>{failure && <ErrorNotice>{failure}</ErrorNotice>}{notice && <Notice tone="success">{notice}</Notice>}
    <section className="surface-card add-skill-card"><div><span className="eyebrow">GROW YOUR PROFILE</span><h3>Add a skill</h3><p>Choose an existing skill from the shared catalog.</p></div><form className="inline-form" onSubmit={addSkill}><select aria-label="Skill catalog" value={selected} required onChange={(event) => setSelected(event.target.value)}><option value="">Choose a skill</option>{available.map((skill) => <option key={skill.id} value={skill.id}>{skill.name}{skill.category ? ` · ${skill.category}` : ''}</option>)}</select><select aria-label="Proficiency" value={level} onChange={(event) => setLevel(event.target.value)}>{PROFICIENCY.map((value) => <option key={value}>{value}</option>)}</select><button className="button button-primary" disabled={busy || !available.length}>{busy ? 'Adding…' : 'Add skill'}</button></form></section>
    {mine.length ? <div className="skills-grid">{mine.map((studentSkill) => {
      const score = scores.get(studentSkill.skill_id); const records = (data.evidence || []).filter((entry) => entry.skill_id === studentSkill.skill_id);
      return <article className="surface-card skill-card" key={studentSkill.id}><div className="skill-card-top"><div className="skill-avatar">{(studentSkill.skill_name || '?').slice(0, 1)}</div><button className="icon-button" title={`Remove ${studentSkill.skill_name}`} aria-label={`Remove ${studentSkill.skill_name}`} onClick={() => removeSkill(studentSkill.skill_id)}>×</button></div><div className="skill-name-row"><div><h3>{studentSkill.skill_name}</h3><small>{studentSkill.skill_category || 'General skill'}</small></div><span className="level-badge">{studentSkill.proficiency}</span></div>
        {score ? <div className="score-stack"><ProgressBar score={score.overall_score} label="Overall score" /><div className="score-breakdown"><span>Proficiency <strong>{score.proficiency_score}</strong></span><span>Evidence <strong>{score.evidence_score}</strong></span></div></div> : <p className="muted-copy">No score available yet.</p>}
        <div className="evidence-list"><div className="evidence-heading">EVIDENCE <span>{records.length}</span></div>{records.length ? records.slice(0, 3).map((entry) => <div className="evidence-item" key={entry.id}><span className="evidence-dot"/><span>{entry.evidence_title}<small>{entry.evidence_type.toLowerCase()} · {entry.verification_status.toLowerCase().replace('_', ' ')}</small></span></div>) : <p className="empty-inline">Evidence will appear here when linked to this skill.</p>}</div>
      </article>;
    })}</div> : <EmptyState title="Your skills start here">Add your first skill from the catalog, then take an assessment or attach evidence to build your profile.</EmptyState>}
  </div>;
}

export function AssessmentsPage() {
  const load = useCallback(() => api.get('/assessments'), []);
  const { data: assessments, loading, error, refresh } = useResource(load, [load]);
  const [active, setActive] = useState(null); const [answers, setAnswers] = useState({}); const [result, setResult] = useState(null);
  const [busy, setBusy] = useState(false); const [failure, setFailure] = useState('');
  async function openAssessment(item) {
    setFailure(''); setResult(null); setAnswers({});
    try { const detail = await api.get(`/assessments/${item.id}`); setActive(detail); setResult(detail.result || null); }
    catch (reason) { setFailure(friendlyError(reason)); }
  }
  async function submit(event) {
    event.preventDefault(); if (!active) return;
    const submittedAnswers = active.questions.map((question) => ({ question_id: question.id, answer: answers[question.id] }));
    if (submittedAnswers.some((answer) => !answer.answer)) { setFailure('Answer every question before submitting.'); return; }
    setBusy(true); setFailure('');
    try { const response = await api.post(`/assessments/${active.id}/submit`, { answers: submittedAnswers }); setResult(response); }
    catch (reason) { setFailure(friendlyError(reason)); }
    finally { setBusy(false); }
  }
  if (loading) return <Loading />;
  return <div className="page-stack"><SectionHeading eyebrow="PRACTICE & PROGRESS" title="Skill assessments" description="Answer questions and let the backend calculate and record your result." />
    <ErrorNotice onRetry={refresh}>{error}</ErrorNotice>{failure && <ErrorNotice>{failure}</ErrorNotice>}
    {active ? <section className="surface-card assessment-detail"><button className="back-link" onClick={() => { setActive(null); setResult(null); }}>← All assessments</button><div className="assessment-detail-head"><div><span className="eyebrow">{active.skill?.name || 'SKILL CHECK'}</span><h2>{active.title}</h2><p>{active.description || 'Choose the best answer for each question.'}</p></div>{result && <div className="result-score"><strong>{result.score}%</strong><small>{result.correct_answers} of {result.total_questions} correct</small></div>}</div>
      <form onSubmit={submit} className="question-list">{active.questions.map((question, index) => {
        const prior = result?.answers?.find((answer) => answer.question_id === question.id);
        return <fieldset className="question-card" key={question.id}><legend><span className="question-number">{String(index + 1).padStart(2, '0')}</span>{question.prompt}</legend><div className="option-list">{question.options.map((option) => <label className={`answer-option ${answers[question.id] === option ? 'chosen' : ''} ${prior?.answer === option ? prior.is_correct ? 'answer-correct' : 'answer-wrong' : ''}`} key={option}><input type="radio" name={`question-${question.id}`} value={option} checked={result ? prior?.answer === option : answers[question.id] === option} disabled={Boolean(result)} onChange={() => setAnswers({ ...answers, [question.id]: option })} /><span className="radio-mark"/>{option}{prior?.answer === option && <span className="answer-result">{prior.is_correct ? 'Correct' : 'Your answer'}</span>}</label>)}</div></fieldset>;
      })}{!result && <button className="button button-primary" disabled={busy}>{busy ? 'Submitting…' : 'Submit assessment'} <span>→</span></button>}{result && <Notice tone="success">Result saved to your account. The score above came from the assessment service.</Notice>}</form>
    </section> : <>{assessments?.length ? <div className="assessment-catalog">{assessments.map((item) => <article className="surface-card assessment-tile" key={item.id}><div className="tile-icon">▤</div><span className="eyebrow">{item.skill.name}</span><h3>{item.title}</h3><p>{item.description || `${item.questions.length} questions to check your current understanding.`}</p><div className="tile-footer"><span>{item.questions.length} questions</span><button className="button button-secondary" onClick={() => openAssessment(item)}>Open assessment <span>→</span></button></div></article>)}</div> : <EmptyState icon="▤" title="No assessments available">When assessments are added to the catalog, you can take them here.</EmptyState>}</>}
  </div>;
}

export function RolesPage() {
  const { targetRoleId, setTargetRoleId } = useSelectedRole();
  const { data, loading, error, refresh } = useRoleData();
  useEffect(() => { if (data?.roles?.length && !data.roles.some((role) => String(role.id) === String(targetRoleId))) setTargetRoleId(String(data.roles[0].id)); }, [data?.roles, targetRoleId, setTargetRoleId]);
  if (loading) return <Loading label="Comparing your skills with available roles…" />;
  const roles = data?.roles || [];
  const active = roles.find((role) => String(role.id) === String(targetRoleId)) || roles[0];
  const match = data?.matches?.find((item) => item.role_id === active?.id);
  return <div className="page-stack"><SectionHeading eyebrow="FIND YOUR DIRECTION" title="Role matching" description="See how your current backend skill scores compare with each role’s requirements." action={<TargetRolePicker roles={roles} value={active?.id || ''} onChange={setTargetRoleId} />} />
    <ErrorNotice onRetry={refresh}>{error}</ErrorNotice>{roles.length ? <>
      <div className="role-overview-grid">{data.matches.map((item) => <button className={`role-summary-card ${String(item.role_id) === String(active?.id) ? 'selected' : ''}`} key={item.role_id} onClick={() => setTargetRoleId(String(item.role_id))}><span className="role-summary-icon">◈</span><span className="role-summary-name">{item.role}</span><strong>{item.match_percentage}<small>%</small></strong><ProgressBar score={item.match_percentage} /><span className="role-summary-foot">{item.skill_gaps?.length || 0} skills to strengthen <span>→</span></span></button>)}</div>
      {match && <section className="surface-card role-detail"><div className="role-detail-heading"><div><span className="eyebrow">DETERMINISTIC ROLE MATCH</span><h2>{match.role}</h2><p>Each score and contribution comes from the Phase 3 skill-intelligence service.</p></div><div className="big-match"><strong>{match.match_percentage}<small>%</small></strong><span>overall match</span></div></div><div className="table-wrap"><table className="data-table"><thead><tr><th>Required skill</th><th>Your score</th><th>Target</th><th>Gap</th><th>Status</th></tr></thead><tbody>{match.required_skills.map((skill) => <tr key={skill.skill_id}><td><strong>{skill.skill}</strong>{skill.missing && <small className="missing-label">MISSING</small>}</td><td>{skill.student_score}</td><td>{skill.required_score}</td><td className={skill.gap ? 'gap-number' : 'good-number'}>{skill.gap}</td><td><span className={`severity severity-${skill.gap_category}`}>{formatSeverity(skill.gap_category)}</span></td></tr>)}</tbody></table></div>
        {match.missing_skills?.length > 0 && <div className="missing-callout"><span>!</span><div><strong>Skills not on your profile</strong><p>{match.missing_skills.join(' · ')}</p></div></div>}
        <a className="button button-primary inline-button" href="/app/recommendations">Explore learning recommendations <span>→</span></a>
      </section>}
    </> : <EmptyState icon="◈" title="No roles are available">Role requirements will appear here when they have been added to the catalog.</EmptyState>}</div>;
}

export function RecommendationsPage() {
  const { targetRoleId, setTargetRoleId } = useSelectedRole();
  const { data: roleData, loading: rolesLoading, error: rolesError } = useRoleData();
  const roles = roleData?.roles || [];
  useEffect(() => { if (roles.length && !roles.some((role) => String(role.id) === String(targetRoleId))) setTargetRoleId(String(roles[0].id)); }, [roles, targetRoleId, setTargetRoleId]);
  const selectedId = roles.find((role) => String(role.id) === String(targetRoleId))?.id;
  const load = useCallback(async () => selectedId ? api.get(`/recommendations?role_id=${selectedId}`) : [], [selectedId]);
  const { data: items, loading, error, refresh } = useResource(load, [load]);
  if (rolesLoading || loading) return <Loading label="Finding your next learning actions…" />;
  return <div className="page-stack"><SectionHeading eyebrow="SMALL STEPS, REAL MOMENTUM" title="Learning recommendations" description="Practical next steps generated from the skill gaps returned by the deterministic backend." action={<TargetRolePicker roles={roles} value={selectedId || ''} onChange={setTargetRoleId} />} />
    <ErrorNotice>{rolesError || error}</ErrorNotice><div className="recommendation-intro"><span className="recommend-icon">✧</span><div><strong>Powered by Phase 3 rules</strong><p>These suggestions use the selected role’s required skills and your current scores. No frontend scores are calculated.</p></div></div>
    {items?.length ? <div className="recommendation-list">{items.map((item, index) => <article className="surface-card recommendation-card" key={item.skill_id}><div className="recommend-rank">{String(index + 1).padStart(2, '0')}</div><div className="recommend-content"><div className="recommend-title"><div><span className="eyebrow">FOCUS SKILL</span><h3>{item.skill}</h3></div><span className={`priority priority-${item.priority}`}>{item.priority} priority</span></div><div className="recommend-metrics"><span>Current <strong>{item.current_score}</strong></span><span>Target <strong>{item.required_score}</strong></span><span>Gap <strong className="gap-number">{item.gap}</strong></span></div><div className="topic-chips">{item.recommended_topics?.map((topic) => <span key={topic}>{topic}</span>)}</div></div><span className="recommend-arrow">↗</span></article>)}</div> : <EmptyState icon="✧" title="You’re on track for this role">There are no outstanding skill gaps for the selected role, or no target role is selected.</EmptyState>}
    <p className="ai-separate-note">Want a personalized explanation or progression plan? <a href="/app/ai">Visit AI Studio →</a></p>
  </div>;
}

function formatSeverity(value) { return ({ meets_requirement: 'Meets target', minor: 'Minor gap', moderate: 'Moderate gap', major: 'Major gap' })[value] || value; }

export function AIStudioPage() {
  const { targetRoleId, setTargetRoleId } = useSelectedRole();
  const { data: roleData, loading: rolesLoading } = useRoleData();
  const roles = roleData?.roles || [];
  const roleId = roles.find((role) => String(role.id) === String(targetRoleId))?.id;
  useEffect(() => { if (roles.length && !roleId) setTargetRoleId(String(roles[0].id)); }, [roles, roleId, setTargetRoleId]);
  const [file, setFile] = useState(null); const [extracting, setExtracting] = useState(false); const [extractResult, setExtractResult] = useState(null);
  const [variant, setVariant] = useState(''); const [normalizing, setNormalizing] = useState(false); const [normalization, setNormalization] = useState(null);
  const [explanation, setExplanation] = useState(null); const [roadmap, setRoadmap] = useState(null); const [aiError, setAiError] = useState('');
  async function extract(event) {
    event.preventDefault(); if (!file) return; setAiError(''); setExtracting(true); setExtractResult(null);
    try {
      const data = new FormData(); data.append('file', file);
      const resume = await api.upload('/students/resume', data);
      const result = await api.post('/ai/resume-skills/extract', { resume_id: resume.id });
      setExtractResult(result);
    } catch (reason) { setAiError(friendlyError(reason)); }
    finally { setExtracting(false); }
  }
  async function normalize(event) {
    event.preventDefault(); setAiError(''); setNormalizing(true); setNormalization(null);
    try { setNormalization(await api.post('/ai/skills/normalize', { variant: variant.trim() })); }
    catch (reason) { setAiError(friendlyError(reason)); } finally { setNormalizing(false); }
  }
  async function askAI(path, setter) {
    if (!roleId) { setAiError('Choose a target role first.'); return; }
    setAiError(''); setter(null);
    try { setter(await api.post(path, { role_id: roleId })); }
    catch (reason) { setAiError(friendlyError(reason)); }
  }
  if (rolesLoading) return <Loading />;
  return <div className="page-stack"><SectionHeading eyebrow="OPTIONAL PERSONALIZED SUPPORT" title="AI Studio" description="Explore your resume and get learning context. Skill scores and gaps always come from the deterministic backend." action={<TargetRolePicker roles={roles} value={roleId || ''} onChange={setTargetRoleId} />} />
    {aiError && <ErrorNotice>{aiError}</ErrorNotice>}
    <div className="ai-safety-banner"><span>✦</span><div><strong>AI suggestions are for guidance</strong><p>They stay separate from verified skills. The numeric results shown here come from Phase 3 and are not changed by AI.</p></div><span className="ai-safety-tag">UNVERIFIED CONTENT IS LABELED</span></div>
    <div className="ai-feature-grid">
      <section className="surface-card ai-feature-card"><div className="feature-topline"><span className="feature-icon feature-violet">⌕</span><span className="feature-state">RESUME TOOL</span></div><h3>Find skills in a resume</h3><p>Upload a PDF or DOCX resume. Suggested skills are matched against the catalog and never added to your profile automatically.</p><form onSubmit={extract} className="upload-drop"><input type="file" accept=".pdf,.docx,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document" onChange={(event) => setFile(event.target.files?.[0] || null)} aria-label="Choose resume PDF or DOCX" /><span className="upload-symbol">↑</span><strong>{file?.name || 'Choose a resume file'}</strong><small>PDF or DOCX · up to 10 MB</small><button className="button button-primary" disabled={!file || extracting}>{extracting ? 'Analyzing resume…' : 'Extract skills'}</button></form>
        {extractResult && <div className="ai-result"><AIStatus result={extractResult} /><strong>Suggested skills</strong>{extractResult.skills?.length ? extractResult.skills.map((skill) => <div className="ai-skill-row" key={skill.skill_id}><span className="ai-skill-check">✧</span><span><strong>{skill.skill}</strong><small>“{skill.evidence}”</small></span><span className="unverified-tag">UNVERIFIED</span></div>) : <p className="muted-copy">No catalog skills were matched to this resume.</p>}<small className="ai-footnote">This result was not saved to your verified skills.</small></div>}</section>
      <section className="surface-card ai-feature-card"><div className="feature-topline"><span className="feature-icon feature-mint">⌁</span><span className="feature-state">CATALOG SUGGESTION</span></div><h3>Normalize a skill name</h3><p>Enter a short form or variation. Suggestions are validated against the existing skill catalog.</p><form onSubmit={normalize} className="normalize-form"><label>Skill variation<input value={variant} onChange={(event) => setVariant(event.target.value)} placeholder="e.g. JS, Javascript" required maxLength={100} /></label><button className="button button-primary" disabled={normalizing || !variant.trim()}>{normalizing ? 'Checking catalog…' : 'Suggest a match'} <span>→</span></button></form>
        {normalization && <div className="ai-result"><AIStatus result={normalization} /><div className="normalization-result"><div><small>ORIGINAL</small><strong>{normalization.variant}</strong></div><span>→</span><div><small>CATALOG MATCH</small><strong>{normalization.normalized_skill || 'No match found'}</strong></div></div>{normalization.normalized_skill && <Notice tone="success">Matched to an existing catalog skill. No skill was created or changed.</Notice>}</div>}</section>
      <section className="surface-card ai-feature-card ai-feature-wide"><div className="feature-topline"><span className="feature-icon feature-peach">◎</span><span className="feature-state">PHASE 3 NUMBERS · AI EXPLANATION</span></div><div className="feature-title-action"><div><h3>Understand your skill gaps</h3><p>Get a practical explanation for the selected role while keeping the original skill scores and gaps intact.</p></div><button className="button button-secondary" disabled={!roleId} onClick={() => askAI('/ai/skill-gaps/explain', setExplanation)}>Explain gaps <span>→</span></button></div>
        {explanation && <div className="ai-result"><AIStatus result={explanation.ai_status} /><div className="gap-explanation-list">{explanation.skill_gaps?.length ? explanation.skill_gaps.map((gap) => <article className="explanation-row" key={gap.skill_id}><div className="explanation-heading"><strong>{gap.skill}</strong><span>{gap.student_score} current · {gap.required_score} required · gap {gap.gap}</span></div><p>{gap.explanation}</p></article>) : <p className="muted-copy">There are no open gaps for this role.</p>}</div></div>}</section>
      <section className="surface-card ai-feature-card ai-feature-wide"><div className="feature-topline"><span className="feature-icon feature-blue">↗</span><span className="feature-state">PERSONALIZED PROGRESSION</span></div><div className="feature-title-action"><div><h3>Build a learning roadmap</h3><p>Use your current skills, project evidence, target role, and Phase 3 gaps to organize what to learn next.</p></div><button className="button button-primary" disabled={!roleId} onClick={() => askAI('/ai/learning-roadmap', setRoadmap)}>Create roadmap <span>→</span></button></div>
        {roadmap && <div className="ai-result"><AIStatus result={roadmap} /><div className="roadmap-match">Phase 3 role match <strong>{roadmap.phase3_match}%</strong></div>{roadmap.steps?.length ? <div className="roadmap-steps">{roadmap.steps.map((step) => <article className="roadmap-step" key={step.skill_id}><span className="step-number">{String(step.sequence).padStart(2, '0')}</span><div><div className="roadmap-step-title"><strong>{step.title}</strong><span className={`priority priority-${step.priority}`}>{step.priority} priority</span></div><small>{step.skill}</small><div className="topic-chips">{step.topics?.map((topic) => <span key={topic}>{topic}</span>)}</div></div></article>)}</div> : <p className="muted-copy">No learning steps are needed for this role right now.</p>}{roadmap.phase3_gaps?.length > 0 && <div className="phase3-values"><strong>Original Phase 3 gaps</strong><span>{roadmap.phase3_gaps.map((item) => `${item.skill}: ${item.gap}`).join(' · ')}</span></div>}</div>}</section>
    </div>
  </div>;
}

function AIStatus({ result }) {
  if (!result) return null;
  const fallback = result.status === 'fallback' || result.ai_status?.status === 'fallback';
  const available = result.ai_available ?? result.ai_status?.ai_available;
  return <div className={`ai-status ${fallback ? 'fallback' : available ? 'available' : 'neutral'}`} role="status"><span>{fallback ? '↻' : available ? '✦' : 'i'}</span><div><strong>{fallback ? 'Showing a safe fallback' : available ? 'Local AI suggestion' : 'Backend result'}</strong>{fallback && <small>{result.fallback_reason || result.ai_status?.fallback_reason || 'The AI response could not be used.'}</small>}</div></div>;
}

const RESOURCE_PATHS = {
  projects: '/students/projects', certifications: '/students/certifications',
  experience: '/students/experience', internships: '/students/internships',
};
const RESOURCE_TITLES = { projects: 'Projects', certifications: 'Certifications', experience: 'Experience', internships: 'Internships' };
const EMPTY_FORMS = {
  projects: { title: '', description: '', technologies: '', project_url: '', github_url: '', role: '' },
  certifications: { name: '', issuing_organization: '', issue_date: '', expiry_date: '', credential_id: '', description: '' },
  experience: { organization: '', job_title: '', employment_type: 'FULL_TIME', location: '', start_date: '', end_date: '', description: '' },
  internships: { organization: '', role: '', start_date: '', end_date: '', internship_type: 'SUMMER', status: 'COMPLETED', description: '' },
};

export function PortfolioPage() {
  const [kind, setKind] = useState('projects');
  const load = useCallback(() => api.get(RESOURCE_PATHS[kind]), [kind]);
  const { data, loading, error, refresh } = useResource(load, [load]);
  const [form, setForm] = useState(EMPTY_FORMS[kind]); const [failure, setFailure] = useState(''); const [busy, setBusy] = useState(false); const [notice, setNotice] = useState('');
  useEffect(() => setForm(EMPTY_FORMS[kind]), [kind]);
  async function createItem(event) {
    event.preventDefault(); setBusy(true); setFailure(''); setNotice('');
    const payload = Object.fromEntries(Object.entries(form).map(([key, value]) => [key, value === '' ? null : value]));
    if (kind === 'projects') payload.skill_ids = [];
    try { await api.post(RESOURCE_PATHS[kind], payload); setForm(EMPTY_FORMS[kind]); setNotice(`${RESOURCE_TITLES[kind].slice(0, -1) || RESOURCE_TITLES[kind]} added.`); await refresh(); }
    catch (reason) { setFailure(friendlyError(reason)); } finally { setBusy(false); }
  }
  async function removeItem(item) {
    if (!window.confirm(`Delete this ${kind === 'experience' ? 'experience' : kind.slice(0, -1)}?`)) return;
    try { await api.delete(`${RESOURCE_PATHS[kind]}/${item.id}`); await refresh(); }
    catch (reason) { setFailure(friendlyError(reason)); }
  }
  const fields = portfolioFields(kind);
  return <div className="page-stack"><SectionHeading eyebrow="YOUR EXPERIENCE, TOGETHER" title="Portfolio" description="Projects, certifications, and work experience help make your skills visible." action={<div className="portfolio-count">{data?.length || 0} {RESOURCE_TITLES[kind].toLowerCase()}</div>} />
    <div className="portfolio-tabs" role="tablist" aria-label="Portfolio section">{Object.keys(RESOURCE_PATHS).map((key) => <button role="tab" aria-selected={kind === key} className={kind === key ? 'active' : ''} key={key} onClick={() => { setKind(key); setFailure(''); setNotice(''); }}>{RESOURCE_TITLES[key]}</button>)}</div>
    {error && <ErrorNotice onRetry={refresh}>{error}</ErrorNotice>}{failure && <ErrorNotice>{failure}</ErrorNotice>}{notice && <Notice tone="success">{notice}</Notice>}
    <div className="portfolio-layout"><section className="surface-card portfolio-form-card"><span className="eyebrow">ADD TO YOUR STORY</span><h3>New {RESOURCE_TITLES[kind].replace(/s$/, '').toLowerCase()}</h3><form onSubmit={createItem} className="form-stack portfolio-form">{fields.map((field) => <label key={field.name}>{field.label}{field.options ? <select name={field.name} value={form[field.name]} onChange={(event) => setForm({ ...form, [field.name]: event.target.value })}>{field.options.map((item) => <option key={item}>{item}</option>)}</select> : field.type === 'textarea' ? <textarea name={field.name} rows="3" value={form[field.name]} onChange={(event) => setForm({ ...form, [field.name]: event.target.value })} /> : <input name={field.name} type={field.type || 'text'} required={field.required} value={form[field.name]} onChange={(event) => setForm({ ...form, [field.name]: event.target.value })} />}</label>)}<button className="button button-primary" disabled={busy}>{busy ? 'Saving…' : 'Save entry'} <span>→</span></button></form></section>
      <section className="portfolio-list">{loading ? <Loading label="Loading your portfolio…" /> : data?.length ? data.map((item) => <article className="surface-card portfolio-item" key={item.id}><div className="portfolio-item-icon">{kind === 'projects' ? '▣' : kind === 'certifications' ? '✧' : '↗'}</div><div className="portfolio-item-body"><div className="portfolio-item-heading"><div><span className="eyebrow">{item.organization || item.issuing_organization || item.role || item.employment_type || RESOURCE_TITLES[kind]}</span><h3>{item.title || item.name || item.job_title || item.role}</h3></div><button className="icon-button" title="Delete entry" aria-label={`Delete ${item.title || item.name || item.job_title || item.role}`} onClick={() => removeItem(item)}>×</button></div><p>{item.description || item.technologies || item.credential_id || 'Add a description to share more about this experience.'}</p><div className="portfolio-meta">{item.start_date || item.issue_date || ''}{item.end_date ? ` — ${item.end_date}` : ''}{item.skills?.length ? ` · ${item.skills.map((skill) => skill.name).join(', ')}` : ''}</div></div></article>) : <EmptyState icon="▣" title={`Your ${RESOURCE_TITLES[kind].toLowerCase()} will show here`}>Add an entry using the form. Keep it specific and connect it to the skills you want to demonstrate.</EmptyState>}</section></div>
  </div>;
}

function portfolioFields(kind) {
  if (kind === 'projects') return [{ name: 'title', label: 'Project title', required: true }, { name: 'role', label: 'Your role' }, { name: 'technologies', label: 'Technologies' }, { name: 'project_url', label: 'Project URL', type: 'url' }, { name: 'github_url', label: 'GitHub URL', type: 'url' }, { name: 'description', label: 'Description', type: 'textarea' }];
  if (kind === 'certifications') return [{ name: 'name', label: 'Certification name', required: true }, { name: 'issuing_organization', label: 'Issuing organization', required: true }, { name: 'issue_date', label: 'Issue date', type: 'date', required: true }, { name: 'expiry_date', label: 'Expiry date', type: 'date' }, { name: 'credential_id', label: 'Credential ID' }, { name: 'description', label: 'Description', type: 'textarea' }];
  if (kind === 'experience') return [{ name: 'organization', label: 'Organization', required: true }, { name: 'job_title', label: 'Job title', required: true }, { name: 'employment_type', label: 'Employment type', options: ['FULL_TIME', 'PART_TIME', 'FREELANCE', 'INTERNSHIP', 'OTHER'] }, { name: 'location', label: 'Location' }, { name: 'start_date', label: 'Start date', type: 'date', required: true }, { name: 'end_date', label: 'End date', type: 'date' }, { name: 'description', label: 'Description', type: 'textarea' }];
  return [{ name: 'organization', label: 'Organization', required: true }, { name: 'role', label: 'Role', required: true }, { name: 'start_date', label: 'Start date', type: 'date', required: true }, { name: 'end_date', label: 'End date', type: 'date' }, { name: 'internship_type', label: 'Internship type', options: ['SUMMER', 'WINTER', 'PART_TIME', 'FULL_TIME', 'REMOTE', 'OTHER'] }, { name: 'status', label: 'Status', options: ['COMPLETED', 'ONGOING', 'PLANNED', 'CANCELLED'] }, { name: 'description', label: 'Description', type: 'textarea' }];
}
