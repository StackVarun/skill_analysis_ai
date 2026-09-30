import { useCallback, useState } from 'react';
import { api, friendlyError } from '../services/api';
import { useResource } from '../hooks/useResource';
const label = value => (value || '').replaceAll('_', ' ').toLowerCase();

function StudentTask({ task, onUpdate, busy }) {
  const [submission, setSubmission] = useState(task.submission || '');
  return <article className="faculty-review-card"><div className="faculty-card-heading"><div><small>{label(task.kind)} · {task.faculty_name}</small><h3>{task.title}</h3></div><span className="faculty-status">{label(task.status)}</span></div><p>{task.description}</p><p>{task.skill || task.project || 'General guidance'} · Due {task.due_date || 'Flexible'}</p>{task.feedback && <p className="faculty-feedback"><strong>Faculty feedback:</strong> {task.feedback}</p>}{['ASSIGNED', 'IN_PROGRESS'].includes(task.status) ? <><label>Submission for {task.title}<textarea rows="3" maxLength="10000" value={submission} onChange={event => setSubmission(event.target.value)} placeholder="Describe your work and paste your project or document link" /></label><div className="faculty-actions">{task.status === 'ASSIGNED' && <button className="button button-secondary" disabled={busy} onClick={() => onUpdate(task.id, 'IN_PROGRESS', submission)}>Start task</button>}<button className="button button-primary" disabled={busy || submission.trim().length < 5} onClick={() => onUpdate(task.id, 'SUBMITTED', submission)}>Submit for faculty review</button></div></> : <><p>{task.submission}</p><small>{task.status === 'COMPLETED' ? 'Your faculty mentor has marked this work completed.' : 'Your submission is awaiting faculty review.'}</small></>}</article>;
}


function StudentReview({ review, onResubmit, busy }) {
  const [response, setResponse] = useState('');
  return <article className="faculty-review-card"><div className="faculty-card-heading"><div><small>{label(review.kind)}</small><h4>{review.title}</h4></div><span className={review.status === 'APPROVED' ? 'faculty-verified' : 'faculty-status'}>{review.status === 'APPROVED' ? '✓ Faculty endorsed' : label(review.status)}</span></div>{review.reviewer && <p>Reviewed by {review.reviewer}</p>}{review.feedback && <p className="faculty-feedback">{review.feedback}</p>}{review.student_response && <p className="faculty-submission">Your response: {review.student_response}</p>}{review.status === 'PENDING' && <p>Your submission is in the faculty inbox.</p>}{review.status === 'CHANGES_REQUESTED' && <><p>{review.kind === 'ASSESSMENT' ? 'Explain your assessment result or the work completed after faculty feedback.' : 'Edit your project or evidence, or respond below to request another review.'}</p><label>Response for {review.title}<textarea rows="3" maxLength="3000" value={response} onChange={event => setResponse(event.target.value)} /></label><button className="button button-primary" disabled={busy || response.trim().length < 5} onClick={() => onResubmit(review.id, response)}>Resubmit verification request</button></>}</article>;
}

export function StudentMentorship() {
  const load = useCallback(async () => {
    const [tasks, reviews] = await Promise.all([api.get('/students/mentorship'), api.get('/students/reviews')]);
    return { tasks, reviews };
  }, []);
  const { data, error, loading, refresh } = useResource(load, [load]);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState('');
  const [failure, setFailure] = useState('');
  async function update(id, status, submission) {
    setBusy(true); setFailure(''); setMessage('');
    try { await api.patch(`/students/mentorship/${id}`, { status, submission }); await refresh(); setMessage(status === 'SUBMITTED' ? 'Work submitted to your faculty mentor.' : 'Task started.'); }
    catch (reason) { setFailure(friendlyError(reason)); }
    finally { setBusy(false); }
  }
  async function resubmit(id, response) {
    setBusy(true); setFailure(''); setMessage('');
    try { await api.post(`/students/reviews/${id}/resubmit`, { response }); await refresh(); setMessage('Verification request sent back to faculty.'); }
    catch (reason) { setFailure(friendlyError(reason)); }
    finally { setBusy(false); }
  }
  return <section className="portal-page faculty-workspace"><div className="faculty-section-heading"><div><h2>Mentorship & reviews</h2><p>Tasks assigned by your faculty, plus feedback on your projects and skills.</p></div><button className="button button-secondary" disabled={loading || busy} onClick={refresh}>Refresh</button></div>{(error || failure) && <p role="alert" className="notice notice-error">{error || failure}</p>}{message && <p role="status" className="notice notice-success">{message}</p>}
    <section className="surface-card faculty-panel"><h3>My mentorship tasks</h3>{loading ? <p>Loading tasks…</p> : data?.tasks?.length ? <div className="faculty-review-grid">{data.tasks.map(task => <StudentTask key={`${task.id}-${task.status}`} task={task} onUpdate={update} busy={busy} />)}</div> : <p>Your faculty mentor has not assigned a task yet.</p>}</section>
    <section className="surface-card faculty-panel"><h3>Faculty verification requests</h3>{loading ? <p>Loading reviews…</p> : data?.reviews?.length ? <div className="faculty-review-grid">{data.reviews.map(review => <StudentReview key={`${review.id}-${review.status}`} review={review} onResubmit={resubmit} busy={busy} />)}</div> : <p>Complete an assessment or add a completed project to request faculty verification automatically.</p>}</section>
  </section>;
}
