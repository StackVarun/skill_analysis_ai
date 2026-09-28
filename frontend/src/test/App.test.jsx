import { describe, expect, it, vi, beforeEach } from 'vitest';
import { fireEvent, render, screen } from '@testing-library/react';
import { readFileSync } from 'node:fs';
import { MemoryRouter, Outlet, Route, Routes } from 'react-router-dom';
import { AuthProvider } from '../context/AuthContext';
import AuthPage from '../pages/AuthPage';
import ProtectedRoute from '../components/ProtectedRoute';
import { AIStudioPage, AssessmentsPage, DashboardPage, RolesPage } from '../pages/WorkspacePages';
import { api, TOKEN_KEY } from '../services/api';

function withAuth(children, initialEntries = ['/']) {
  return render(<MemoryRouter initialEntries={initialEntries}><AuthProvider>{children}</AuthProvider></MemoryRouter>);
}

describe('student workspace frontend', () => {
  beforeEach(() => { vi.restoreAllMocks(); });

  it('redirects a protected route to login when there is no JWT', async () => {
    withAuth(<Routes><Route element={<ProtectedRoute />}><Route path="/private" element={<p>Private dashboard</p>} /></Route><Route path="/login" element={<p>Login page</p>} /></Routes>, ['/private']);
    expect(await screen.findByText('Login page')).toBeInTheDocument();
    expect(screen.queryByText('Private dashboard')).not.toBeInTheDocument();
  });

  it('registers and stores a student JWT through the backend auth endpoint', async () => {
    vi.spyOn(api, 'post').mockResolvedValue({ access_token: 'server-token', user: { id: 4, first_name: 'Mina', full_name: 'Mina Patel' } });
    withAuth(<Routes><Route path="/register" element={<AuthPage mode="register" />} /><Route path="/app" element={<p>Workspace home</p>} /></Routes>, ['/register']);
    fireEvent.change(screen.getByLabelText('First name'), { target: { value: 'Mina' } });
    fireEvent.change(screen.getByLabelText('Last name'), { target: { value: 'Patel' } });
    fireEvent.change(screen.getByLabelText('Email address'), { target: { value: 'mina@example.com' } });
    fireEvent.change(screen.getByLabelText('Password'), { target: { value: 'password123' } });
    fireEvent.click(screen.getByRole('button', { name: /create student account/i }));
    expect(await screen.findByText('Workspace home')).toBeInTheDocument();
    expect(localStorage.getItem(TOKEN_KEY)).toBe('server-token');
    expect(api.post).toHaveBeenCalledWith('/auth/register', expect.objectContaining({ role: 'STUDENT', email: 'mina@example.com' }));
  });

  it('logs in through the backend and stores its JWT', async () => {
    vi.spyOn(api, 'post').mockResolvedValue({ access_token: 'login-token', user: { id: 4, first_name: 'Mina' } });
    withAuth(<Routes><Route path="/login" element={<AuthPage mode="login" />} /><Route path="/app" element={<p>Workspace home</p>} /></Routes>, ['/login']);
    fireEvent.change(screen.getByLabelText('Email address'), { target: { value: 'mina@example.com' } });
    fireEvent.change(screen.getByLabelText('Password'), { target: { value: 'password123' } });
    fireEvent.click(screen.getByRole('button', { name: /sign in/i }));
    expect(await screen.findByText('Workspace home')).toBeInTheDocument();
    expect(localStorage.getItem(TOKEN_KEY)).toBe('login-token');
    expect(api.post).toHaveBeenCalledWith('/auth/login', { email: 'mina@example.com', password: 'password123' });
  });

  it('renders dashboard metrics and role recommendations from backend responses', async () => {
    vi.spyOn(api, 'get').mockImplementation(async (path) => {
      if (path === '/students/profile') return { full_name: 'Mina Patel', institution: 'North College' };
      if (path === '/students/skills') return [{ id: 1, skill: { name: 'Python' } }];
      if (path === '/skills/scores') return [{ skill: 'Python', overall_score: 76 }];
      if (path === '/roles') return [{ id: 3, name: 'Backend Developer' }];
      if (path === '/roles/3/match') return { role_id: 3, role: 'Backend Developer', match_percentage: 63.5, skill_gaps: [{ skill: 'Docker' }] };
      if (path === '/assessments' || path === '/students/skill-evidence' || path === '/students/projects' || path === '/assessments/3') return [];
      if (path === '/skill-gaps?role_id=3') return { match_percentage: 63.5, missing_skills: ['Docker'], skill_gaps: [{ skill: 'Docker' }] };
      if (path === '/recommendations?role_id=3') return [{ skill_id: 8, skill: 'Docker', priority: 'HIGH', recommended_topics: ['Images and containers'] }];
      throw new Error(`Unexpected ${path}`);
    });
    withAuth(<DashboardPage />);
    expect(await screen.findByText(/Good (morning|afternoon|evening), Mina\./)).toBeInTheDocument();
    expect(await screen.findByText('76%')).toBeInTheDocument();
    expect((screen.getAllByText('Backend Developer')).length).toBeGreaterThan(0);
    expect(screen.getByText('Build Docker')).toBeInTheDocument();
    expect((screen.getAllByText('63.5')).length).toBeGreaterThan(0);
  });

  it('submits assessment answers without calculating the score in the UI', async () => {
    vi.spyOn(api, 'get').mockImplementation(async (path) => {
      if (path === '/assessments') return [{ id: 2, title: 'Python basics', skill: { name: 'Python' }, questions: [{ id: 9 }] }];
      if (path === '/assessments/2') return { id: 2, title: 'Python basics', skill: { name: 'Python' }, questions: [{ id: 9, prompt: 'Which is a Python list?', options: ['[]', '{}'] }] };
      throw new Error(`Unexpected ${path}`);
    });
    vi.spyOn(api, 'post').mockResolvedValue({ id: 12, score: 100, correct_answers: 1, total_questions: 1, answers: [{ question_id: 9, answer: '[]', is_correct: true }] });
    withAuth(<AssessmentsPage />);
    fireEvent.click(await screen.findByRole('button', { name: /open assessment/i }));
    fireEvent.click(await screen.findByLabelText('[]'));
    fireEvent.click(screen.getByRole('button', { name: /submit assessment/i }));
    expect(await screen.findByText('100%')).toBeInTheDocument();
    expect(api.post).toHaveBeenCalledWith('/assessments/2/submit', { answers: [{ question_id: 9, answer: '[]' }] });
  });

  it('renders backend role-match and gap values as returned', async () => {
    vi.spyOn(api, 'get').mockImplementation(async (path) => {
      if (path === '/roles') return [{ id: 3, name: 'Backend Developer' }];
      if (path === '/roles/3/match') return { role_id: 3, role: 'Backend Developer', match_percentage: 63.5, missing_skills: ['Docker'], skill_gaps: [{ skill_id: 1, skill: 'Python', gap: 15 }], required_skills: [{ skill_id: 1, skill: 'Python', student_score: 65, required_score: 80, gap: 15, gap_category: 'moderate', missing: false }] };
      throw new Error(`Unexpected ${path}`);
    });
    withAuth(<RolesPage />);
    expect((await screen.findAllByText('63.5')).length).toBeGreaterThan(0);
    expect(screen.getByText('15')).toBeInTheDocument();
    expect(screen.getByText('Docker')).toBeInTheDocument();
  });

  it('provides tablet and mobile layout breakpoints with a mobile navigation bar', () => {
    const css = readFileSync('src/styles.css', 'utf8');
    expect(css).toContain('@media(max-width:820px)');
    expect(css).toContain('@media(max-width:580px)');
    expect(css).toMatch(/\.mobile-nav\s*\{[^}]*position:fixed/s);
  });

  it('labels an AI fallback response clearly', async () => {
    vi.spyOn(api, 'get').mockImplementation(async (path) => {
      if (path === '/roles') return [{ id: 3, name: 'Backend Developer' }];
      if (path === '/roles/3/match') return { role_id: 3, role: 'Backend Developer', match_percentage: 50, skill_gaps: [] };
      throw new Error(`Unexpected ${path}`);
    });
    vi.spyOn(api, 'post').mockResolvedValue({ role_id: 3, ai_status: { status: 'fallback', ai_available: false, fallback_reason: 'Local AI is unavailable.' }, skill_gaps: [] });
    function Shell() { return <Outlet context={{ targetRoleId: '3', setTargetRoleId: vi.fn() }} />; }
    withAuth(<Routes><Route element={<Shell />}><Route path="/" element={<AIStudioPage />} /></Route></Routes>);
    fireEvent.click(await screen.findByRole('button', { name: /explain gaps/i }));
    expect(await screen.findByText('Showing a safe fallback')).toBeInTheDocument();
    expect(screen.getByText('Local AI is unavailable.')).toBeInTheDocument();
  });

  it('clears a stale token when an authenticated request returns 401', async () => {
    localStorage.setItem(TOKEN_KEY, 'expired-token');
    const originalFetch = globalThis.fetch;
    globalThis.fetch = vi.fn().mockResolvedValue({ status: 401, ok: false, json: async () => ({ message: 'Token expired' }) });
    const listener = vi.fn(); window.addEventListener('skillbridge:unauthorized', listener);
    await expect(api.get('/auth/me')).rejects.toMatchObject({ status: 401 });
    expect(listener).toHaveBeenCalled();
    globalThis.fetch = originalFetch;
    window.removeEventListener('skillbridge:unauthorized', listener);
  });
});
