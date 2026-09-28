import { useState } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { friendlyError } from '../services/api';

export default function AuthPage({ mode }) {
  const registering = mode === 'register';
  const { login, register } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [form, setForm] = useState({ email: '', password: '', first_name: '', last_name: '' });
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  const change = (event) => setForm({ ...form, [event.target.name]: event.target.value });
  async function submit(event) {
    event.preventDefault(); setError(''); setBusy(true);
    try {
      if (registering) await register(form); else await login({ email: form.email, password: form.password });
      navigate(location.state?.from?.pathname || '/app', { replace: true });
    } catch (reason) { setError(friendlyError(reason)); }
    finally { setBusy(false); }
  }
  return <main className="auth-screen">
    <section className="auth-story"><Link to="/login" className="brand auth-brand"><span className="brand-mark">S</span><span>skillbridge<span className="brand-dot">.</span><small>STUDENT WORKSPACE</small></span></Link><div className="story-copy"><span className="story-kicker">YOUR NEXT CHAPTER STARTS HERE</span><h1>Make your skills<br />move you forward.</h1><p>A clear view of what you know, where you’re headed, and what to learn next.</p><div className="story-visual"><div className="visual-orbit orbit-one" /><div className="visual-orbit orbit-two" /><span className="orbit-star">✦</span><div className="floating-card"><span className="mini-icon">↗</span><div><small>CAREER MOMENTUM</small><strong>Built around you</strong></div><span className="sparkline">⌁</span></div><div className="visual-caption">A more intentional path to your next opportunity.</div></div></div><div className="story-footer">SKILLBRIDGE <span>•</span> LEARN WITH DIRECTION</div></section>
    <section className="auth-panel"><div className="auth-panel-inner"><div className="auth-mobile-brand"><span className="brand-mark">S</span> skillbridge</div><div className="auth-heading"><span className="eyebrow">{registering ? 'CREATE YOUR SPACE' : 'WELCOME BACK'}</span><h2>{registering ? 'Start building your path' : 'Good to see you again'}</h2><p>{registering ? 'Set up your student workspace in a few moments.' : 'Sign in to pick up where your progress left off.'}</p></div>
    {error && <div className="notice notice-error" role="alert">{error}</div>}
    <form className="form-stack auth-form" onSubmit={submit}>
      {registering && <div className="form-row"><label>First name<input name="first_name" value={form.first_name} onChange={change} autoComplete="given-name" required maxLength={100} /></label><label>Last name<input name="last_name" value={form.last_name} onChange={change} autoComplete="family-name" required maxLength={100} /></label></div>}
      <label>Email address<input type="email" name="email" value={form.email} onChange={change} autoComplete="email" required maxLength={120} placeholder="you@example.com" /></label>
      <label>Password<input type="password" name="password" value={form.password} onChange={change} autoComplete={registering ? 'new-password' : 'current-password'} required minLength={registering ? 8 : undefined} maxLength={100} placeholder={registering ? 'At least 8 characters' : 'Enter your password'} /></label>
      {registering && <p className="form-hint">Creating an account gives you a student workspace. Your password is sent securely to the SkillBridge backend.</p>}
      <button className="button button-primary button-wide" disabled={busy}>{busy ? <><span className="button-spinner" />Working…</> : registering ? 'Create student account' : 'Sign in'}<span>→</span></button>
    </form><p className="auth-switch">{registering ? 'Already have an account?' : 'New to SkillBridge?'} <Link to={registering ? '/login' : '/register'}>{registering ? 'Sign in' : 'Create an account'}</Link></p><p className="auth-privacy">Your student information stays in your account.</p></div></section>
  </main>;
}
