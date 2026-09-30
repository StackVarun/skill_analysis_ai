import { useEffect, useState } from 'react';
import { api, friendlyError } from '../services/api';
import { IndustryWorkspace } from './IndustryWorkspace';
export { IndustryWorkspace };

function useLoad(path) {
  const [data,setData]=useState(null),[error,setError]=useState(''),[busy,setBusy]=useState(true);
  const refresh=()=>{setBusy(true);api.get(path).then(setData).catch(e=>setError(friendlyError(e))).finally(()=>setBusy(false));};
  useEffect(refresh,[path]);return {data,error,busy,refresh};
}
const Notice=({error})=>error?<p role="alert" className="notice notice-error">{error}</p>:null;
const Match=({match})=>match?<div><strong>{match.match_percentage}% match</strong><div className="portal-tags">{match.required_skills.map(s=><span key={s.skill_id}>{s.skill}: {s.student_score}/{s.required_score}</span>)}</div>{match.skill_gaps.length>0&&<small>Gaps: {match.skill_gaps.map(s=>s.skill).join(', ')}</small>}</div>:null;
const APPLICATION_LABELS={APPLIED:'Applied',REVIEWING:'Reviewing',SHORTLISTED:'Shortlisted',INTERVIEW:'Interview',OFFER:'Offer',REJECTED:'Rejected'};
const APPLICATION_NEXT={APPLIED:['REVIEWING','SHORTLISTED','REJECTED'],REVIEWING:['SHORTLISTED','INTERVIEW','REJECTED'],SHORTLISTED:['INTERVIEW','OFFER','REJECTED'],INTERVIEW:['OFFER','REJECTED'],OFFER:[],REJECTED:[]};
function ApplicationStatusControl({application,onUpdate}){
  const [next,setNext]=useState(application.status);
  useEffect(()=>setNext(application.status),[application.status]);
  const choices=APPLICATION_NEXT[application.status]||[];
  return <div className="application-status-control"><label>Status<select aria-label={`Update status for ${application.student.full_name||'applicant'}`} value={next} onChange={e=>setNext(e.target.value)}><option value={application.status}>{APPLICATION_LABELS[application.status]||application.status}</option>{choices.map(status=><option value={status} key={status}>{APPLICATION_LABELS[status]}</option>)}</select></label><button className="button button-secondary" disabled={next===application.status} onClick={()=>onUpdate(application.id,next)}>Update</button></div>;
}
function ApplicationTracker({status}){
  const steps=['APPLIED','REVIEWING','INTERVIEW','OFFER'];
  if(status==='REJECTED')return <div className="application-tracker rejected"><strong>Application rejected</strong><small>The employer has closed this application.</small></div>;
  const activeIndex=Math.max(0,steps.indexOf(status==='SHORTLISTED'?'REVIEWING':status));
  return <div className="application-tracker" aria-label={`Application status: ${APPLICATION_LABELS[status]||status}`}><div className="application-tracker-heading"><span>Application status</span><strong>{APPLICATION_LABELS[status]||status}</strong></div><ol>{steps.map((step,index)=><li className={index<=activeIndex?'complete':''} key={step}><span>{index<activeIndex?'✓':index+1}</span><small>{APPLICATION_LABELS[step]}</small></li>)}</ol></div>;
}

export function StudentOpportunities(){
  const {data,error,busy,refresh}=useLoad('/opportunities');const applications=useLoad('/applications/mine');const [message,setMessage]=useState('');
  async function apply(id){try{await api.post(`/opportunities/${id}/apply`,{});setMessage('Application submitted.');applications.refresh();refresh();}catch(e){setMessage(friendlyError(e));}}
  const applied=new Map((applications.data||[]).map(a=>[a.opportunity_id,a.status]));
  return <section className="portal-page"><h2>Jobs & internships</h2><p>Explore open opportunities and track your applications.</p><Notice error={error}/>{message&&<p role="status">{message}</p>}{busy?<p>Loading…</p>:(data||[]).length===0?<p>No open opportunities yet.</p>:<div className="portal-grid">{data.map(p=><article className="surface-card portal-card" key={p.id}><small>{p.kind} · {p.company.name}</small><h3>{p.title}</h3><p>{p.description}</p><div className="portal-tags">{p.required_skills.map(s=><span key={s.skill_id}>{s.skill}</span>)}</div><p>{p.location||'Location flexible'} · Deadline {p.deadline||'Open'}</p><button className="button button-primary" disabled={!!applied.get(p.id)} onClick={()=>apply(p.id)}>{APPLICATION_LABELS[applied.get(p.id)]||'Apply'}</button></article>)}</div>}
  <h3>My applications</h3>{(applications.data||[]).map(a=><article className="surface-card application-record" key={a.id}><div><h4>{a.opportunity.title}</h4><small>{a.opportunity.company.name} · {a.opportunity.kind}</small></div><ApplicationTracker status={a.status}/></article>)}</section>;
}


