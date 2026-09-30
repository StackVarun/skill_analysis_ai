import { useCallback, useEffect, useRef, useState } from 'react';
import { api, friendlyError } from '../services/api';

const EMPTY_TASK = { kind: 'COURSEWORK', title: '', description: '', skill_id: '', project_id: '', due_date: '' };
const label = value => (value || '').replaceAll('_', ' ').toLowerCase();

function ReviewCard({ item, onReview, busy }) {
  const [feedback, setFeedback] = useState('');
  const project = item.project;
  return <article className="faculty-review-card">
    <div className="faculty-card-heading"><div><small>{label(item.kind)} · {item.student.full_name || 'Student'}</small><h3>{item.title}</h3></div><span className={item.status === 'APPROVED' ? 'faculty-verified' : 'faculty-status'}>{item.status === 'APPROVED' ? '✓ Endorsed' : label(item.status)}</span></div>
    {project && <><p>{project.description || 'No description supplied.'}</p><p>{project.technologies || 'No technologies listed.'}</p><div className="portal-tags">{(project.skills || []).map(skill => <span key={skill.id}>{skill.name}</span>)}</div><div className="portfolio-links">{project.github_url && <a href={project.github_url} target="_blank" rel="noreferrer">View GitHub ↗</a>}{project.project_url && <a href={project.project_url} target="_blank" rel="noreferrer">Open project ↗</a>}</div></>}
    {item.assessment && <p><strong>{item.assessment.score}%</strong> on {item.assessment.skill} · {item.assessment.correct_answers}/{item.assessment.total_questions} correct answers</p>}
    {item.evidence && <><p>{item.evidence.skill_name}: {item.evidence.description || item.evidence.evidence_title}</p>{item.evidence.source_url && <a href={item.evidence.source_url} target="_blank" rel="noreferrer">Inspect evidence ↗</a>}</>}
    {item.student_response && <div className="faculty-submission"><strong>Student response</strong><p>{item.student_response}</p></div>}
    {item.status === 'PENDING' ? <><label>Review feedback for {item.title}<textarea rows="2" maxLength="3000" value={feedback} onChange={event => setFeedback(event.target.value)} placeholder="Explain your endorsement or requested changes" /></label><div className="faculty-actions"><button className="button button-primary" disabled={busy} onClick={() => onReview(item.id, 'APPROVED', feedback, item.updated_at)}>✓ Approve</button><button className="button button-secondary" disabled={busy || !feedback.trim()} onClick={() => onReview(item.id, 'CHANGES_REQUESTED', feedback, item.updated_at)}>Request changes</button></div></> : <p className="faculty-feedback">{item.reviewer && `Reviewed by ${item.reviewer}. `}{item.feedback || 'No feedback added.'}</p>}
  </article>;
}

function FacultyTask({ task, onReview, busy }) {
  const [feedback, setFeedback] = useState('');
  return <article className="faculty-review-card"><div className="faculty-card-heading"><div><small>{task.student_name} · {label(task.kind)}</small><h3>{task.title}</h3></div><span className="faculty-status">{label(task.status)}</span></div><p>{task.description}</p><small>{task.skill || task.project || 'General guidance'} · Due {task.due_date || 'Flexible'}</small>{task.submission && <div className="faculty-submission"><strong>Student submission</strong><p>{task.submission}</p></div>}{task.feedback && <p className="faculty-feedback">Your feedback: {task.feedback}</p>}{task.status === 'SUBMITTED' && <><label>Task feedback for {task.title}<textarea rows="2" value={feedback} maxLength="3000" onChange={event => setFeedback(event.target.value)} /></label><div className="faculty-actions"><button className="button button-primary" disabled={busy} onClick={() => onReview(task.id, 'COMPLETED', feedback)}>Mark completed</button><button className="button button-secondary" disabled={busy || !feedback.trim()} onClick={() => onReview(task.id, 'IN_PROGRESS', feedback)}>Return for revision</button></div></>}</article>;
}

export function FacultyDashboard({ opportunities }) {
  const [data, setData] = useState({ summary: null, students: [], reviews: [], tasks: [], skills: [] });
  const [error, setError] = useState('');
  const [message, setMessage] = useState('');
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [studentId, setStudentId] = useState('');
  const [detail, setDetail] = useState(null);
  const [loadingStudent, setLoadingStudent] = useState(false);
  const [task, setTask] = useState(EMPTY_TASK);
  const [reviewFilter, setReviewFilter] = useState('PENDING');
  const [studentSearch, setStudentSearch] = useState('');
  const detailRequest = useRef(0);

  const refresh = useCallback(async (quiet = false) => {
    if (!quiet) setLoading(true);
    const keys = ['summary', 'students', 'reviews', 'tasks', 'skills'];
    const paths = ['/faculty/summary', '/faculty/students', '/faculty/reviews', '/faculty/tasks', '/skills'];
    const results = await Promise.allSettled(paths.map(path => api.get(path)));
    setData(previous => Object.fromEntries(keys.map((key, index) => [key, results[index].status === 'fulfilled' ? results[index].value : previous[key]])));
    const failed = results.find(result => result.status === 'rejected');
    if (failed) setError(friendlyError(failed.reason));
    else setError('');
    if (!quiet) setLoading(false);
  }, []);
  useEffect(() => {
    refresh();
    const onProfile = () => { ++detailRequest.current; setStudentId(''); setDetail(null); setData({ summary: null, students: [], reviews: [], tasks: [], skills: [] }); refresh(); };
    window.addEventListener('skillbridge:faculty-profile', onProfile);
    const timer = window.setInterval(() => { if (document.visibilityState === 'visible') refresh(true); }, 30000);
    return () => { window.clearInterval(timer); window.removeEventListener('skillbridge:faculty-profile', onProfile); };
  }, [refresh]);

  async function loadStudent(id) {
    const version = ++detailRequest.current;
    setStudentId(id); setDetail(null); setTask(EMPTY_TASK);
    if (!id) { setLoadingStudent(false); return; }
    setLoadingStudent(true);
    try { const result = await api.get(`/faculty/students/${id}`); if (version === detailRequest.current) setDetail(result); }
    catch (reason) { if (version === detailRequest.current) setError(friendlyError(reason)); }
    finally { if (version === detailRequest.current) setLoadingStudent(false); }
  }
  async function run(action, success) {
    setBusy(true); setMessage(''); setError('');
    try { await action(); await refresh(true); if (studentId) setDetail(await api.get(`/faculty/students/${studentId}`)); setMessage(success); }
    catch (reason) { setError(friendlyError(reason)); }
    finally { setBusy(false); }
  }
  const review = (id, decision, feedback, expected_updated_at) => run(() => api.post(`/faculty/reviews/${id}/decision`, { decision, feedback, expected_updated_at }), decision === 'APPROVED' ? 'Faculty endorsement saved. The student passport has been updated.' : 'Changes requested. The student can see your feedback.');
  const reviewTask = (id, status, feedback) => run(() => api.patch(`/faculty/tasks/${id}`, { status, feedback }), status === 'COMPLETED' ? 'Task completed.' : 'Task returned with feedback.');
  function assign(event) {
    event.preventDefault();
    run(async () => {
      await api.post('/faculty/tasks', { ...task, student_id: Number(studentId), skill_id: task.skill_id ? Number(task.skill_id) : null, project_id: task.kind === 'PROJECT_SUPERVISION' && task.project_id ? Number(task.project_id) : null, due_date: task.due_date || null });
      setTask(EMPTY_TASK);
    }, 'Task assigned. The student can see it in Mentorship & reviews.');
  }
  const summary = data.summary || {};
  const filteredReviews = data.reviews.filter(item => reviewFilter === 'ALL' || item.status === reviewFilter);
  const supervised = data.tasks.filter(item => item.kind === 'PROJECT_SUPERVISION');
  return <div className="faculty-workspace">
    <header className="faculty-welcome"><div><span className="eyebrow">ACADEMICIAN WORKSPACE</span><h2>Guide students from skills to opportunities</h2><p>Endorse completed work, address skill gaps and supervise projects within your institution.</p></div><button className="button button-secondary" disabled={loading || busy} onClick={() => refresh()}>Refresh dashboard</button></header>
    {error && <p role="alert" className="notice notice-error">{error}</p>}{message && <p role="status" className="notice notice-success">{message}</p>}
    <div className="faculty-metrics">{[['Students', summary.student_count], ['Selected students', summary.selected_students], ['At interview stage', summary.interview_students], ['Students with offers', summary.offer_students], ['Verification requests', summary.pending_verifications], ['Active supervision', summary.supervised_projects]].map(([title, value]) => <article className="surface-card" key={title}><small>{title}</small><strong>{loading ? '…' : value ?? '—'}</strong></article>)}</div>
    <p className="muted-copy">Selected includes students currently shortlisted, at interview stage or with an offer. Counts show current application stages; a student may appear in more than one stage across different applications.</p>
    <section className="surface-card faculty-panel" aria-label="Faculty notifications"><div className="faculty-section-heading"><div><h2>Verification inbox</h2><p>{summary.pending_verifications ?? 0} pending notifications · new completed projects, assessments and skill evidence appear here.</p></div><label>Review status<select value={reviewFilter} onChange={event => setReviewFilter(event.target.value)}><option value="PENDING">Pending</option><option value="APPROVED">Approved</option><option value="CHANGES_REQUESTED">Changes requested</option><option value="ALL">All requests</option></select></label></div>
      {loading ? <p>Loading verification requests…</p> : filteredReviews.length ? <div className="faculty-review-grid">{filteredReviews.map(item => <ReviewCard key={`${item.id}-${item.updated_at}`} item={item} onReview={review} busy={busy} />)}</div> : <p>No requests in this view. Completed work will appear automatically.</p>}
    </section>
    <section className="surface-card faculty-panel"><div className="faculty-section-heading"><div><h2>Student skill gaps & mentorship</h2><p>Inspect a student's requirements and assign a focused task.</p></div></div>
      <div className="faculty-student-pickers"><label>Search students<input type="search" value={studentSearch} onChange={event => setStudentSearch(event.target.value)} placeholder="Name or branch" /></label><label>Choose student<select value={studentId} onChange={event => loadStudent(event.target.value)}><option value="">Select a student</option>{data.students.filter(student => student.id === Number(studentId) || `${student.full_name} ${student.branch}`.toLowerCase().includes(studentSearch.toLowerCase())).map(student => <option key={student.id} value={student.id}>{student.full_name || `Student ${student.id}`} · {student.email || `#${student.id}`}</option>)}</select></label></div>
      {loadingStudent && <p>Loading student gaps…</p>}
      {detail && <div className="faculty-mentorship-grid"><div><h3>{detail.student.full_name} {detail.endorsements?.has_endorsements && <span className="faculty-verified">✓ Endorsed items</span>}</h3><p>{detail.student.branch} · {detail.student.graduation_year || 'Graduation year not set'}</p><h4>Open skill gaps</h4>{detail.gaps?.length ? <div className="faculty-gap-list">{detail.gaps.map(gap => <article key={gap.skill_id}><div><strong>{gap.skill}</strong><small>{gap.current_score}/100 current · {gap.required_score}/100 target · gap {gap.gap} · {gap.source || 'Role catalog'}</small></div><button type="button" className="button button-secondary" onClick={() => setTask({ ...EMPTY_TASK, skill_id: String(gap.skill_id), title: `Practice ${gap.skill}`, description: (gap.recommended_topics || []).join('; ') })}>Assign task for {gap.skill}</button></article>)}</div> : <p>No open gaps in the role catalog or applied jobs. Choose a skill below for additional mentoring.</p>}<h4>Applications</h4>{detail.applications?.length ? detail.applications.map(application => <p key={application.id}>{application.title} · {application.company} · <strong>{label(application.status)}</strong></p>) : <p>No applications yet.</p>}</div>
        <form className="form-stack faculty-task-form" onSubmit={assign}><h3>Allocate mentorship</h3><label>Task type<select value={task.kind} onChange={event => setTask({ ...task, kind: event.target.value })}><option value="COURSEWORK">Targeted coursework</option><option value="RESEARCH">Research task</option><option value="PROJECT_SUPERVISION">Project supervision</option></select></label><label>Target skill<select required={task.kind !== 'PROJECT_SUPERVISION'} value={task.skill_id} onChange={event => setTask({ ...task, skill_id: event.target.value })}><option value="">Choose a skill</option>{data.skills.map(skill => <option key={skill.id} value={skill.id}>{skill.name}</option>)}</select></label>{task.kind === 'PROJECT_SUPERVISION' && <label>Project to supervise<select required value={task.project_id} onChange={event => setTask({ ...task, project_id: event.target.value })}><option value="">Choose a project</option>{(detail.projects || []).map(project => <option key={project.id} value={project.id}>{project.title}</option>)}</select></label>}<label>Task title<input required minLength="2" maxLength="200" value={task.title} onChange={event => setTask({ ...task, title: event.target.value })} /></label><label>Task instructions<textarea required minLength="5" maxLength="10000" rows="4" value={task.description} onChange={event => setTask({ ...task, description: event.target.value })} /></label><label>Due date<input type="date" value={task.due_date} onChange={event => setTask({ ...task, due_date: event.target.value })} /></label><button className="button button-primary" disabled={busy}>Assign mentorship task</button></form>
      </div>}
    </section>
    <section className="surface-card faculty-panel"><h2>Project supervision</h2><p>{supervised.length} allocation(s), including completed supervision.</p>{supervised.length ? <div className="faculty-review-grid">{supervised.map(item => <FacultyTask key={`${item.id}-${item.status}`} task={item} onReview={reviewTask} busy={busy} />)}</div> : <p>Select a student and choose Project supervision to allocate a project to yourself.</p>}</section>
    <section className="surface-card faculty-panel"><h2>Coursework & research tasks</h2>{data.tasks.some(item => item.kind !== 'PROJECT_SUPERVISION') ? <div className="faculty-review-grid">{data.tasks.filter(item => item.kind !== 'PROJECT_SUPERVISION').map(item => <FacultyTask key={`${item.id}-${item.status}`} task={item} onReview={reviewTask} busy={busy} />)}</div> : <p>No tasks assigned yet.</p>}</section>
    {opportunities}
  </div>;
}
