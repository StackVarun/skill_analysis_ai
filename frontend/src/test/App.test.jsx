import { useState } from 'react';
import { describe, expect, it, vi, beforeEach } from 'vitest';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { readFileSync } from 'node:fs';
import { MemoryRouter, Outlet, Route, Routes } from 'react-router-dom';
import { AuthProvider, useAuth } from '../context/AuthContext';
import AuthPage from '../pages/AuthPage';
import ProtectedRoute from '../components/ProtectedRoute';
import { AIStudioPage, AssessmentsPage, DashboardPage, ProfilePage, RolesPage, PortfolioPage } from '../pages/WorkspacePages';
import { SkillPassport, InstitutionWorkspace } from '../pages/AdditionalPages';
import { IndustryWorkspace, StudentOpportunities } from '../pages/OpportunityPages';
import { api, TOKEN_KEY } from '../services/api';

function withAuth(children, initialEntries = ['/']) {
  return render(<MemoryRouter initialEntries={initialEntries}><AuthProvider>{children}</AuthProvider></MemoryRouter>);
}

describe('student workspace frontend', () => {
  beforeEach(() => { vi.restoreAllMocks(); localStorage.clear(); });

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

  it('saves only editable profile fields and omits server metadata', async () => {
    vi.spyOn(api, 'get').mockResolvedValue({ id: 9, user_id: 4, full_name: 'Mina Patel', phone: '1234567890', institution: 'North College', created_at: '2026-01-01', updated_at: '2026-01-02' });
    vi.spyOn(api, 'put').mockResolvedValue({ id: 9, user_id: 4, full_name: 'Mina Patel' });
    withAuth(<ProfilePage />);
    await waitFor(() => expect(screen.getByLabelText('Full name')).toHaveValue('Mina Patel'));
    fireEvent.click(screen.getByRole('button', { name: /save profile/i }));
    await waitFor(() => expect(api.put).toHaveBeenCalled());
    const [, sent] = api.put.mock.calls[0];
    expect(sent).toMatchObject({ full_name: 'Mina Patel', institution: 'North College' });
    expect(sent).not.toHaveProperty('id');
    expect(sent).not.toHaveProperty('user_id');
    expect(sent).not.toHaveProperty('created_at');
    expect(sent).not.toHaveProperty('updated_at');
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


it('keeps the newly selected target role after dashboard data reloads', async () => {
  vi.spyOn(api, 'get').mockImplementation(async (path) => {
    if (path === '/students/profile') return { full_name: 'James Smith' };
    if (path === '/roles') return [{ id: 1, name: 'Backend Developer' }, { id: 2, name: 'Frontend Developer' }];
    if (path.includes('/match')) return { role_id: Number(path.split('/')[2]), role: 'Developer', match_percentage: 50, skill_gaps: [] };
    if (path.startsWith('/skill-gaps')) return { match_percentage: 50, skill_gaps: [], missing_skills: [] };
    return [];
  });
  function RoleShell() {
    const [targetRoleId, setTargetRoleId] = useState('1');
    return <><output data-testid="chosen-role">{targetRoleId}</output><Outlet context={{ targetRoleId, setTargetRoleId }} /></>;
  }
  withAuth(<Routes><Route element={<RoleShell />}><Route path="/" element={<DashboardPage />} /></Route></Routes>);
  fireEvent.change(await screen.findByLabelText('Target role'), { target: { value: '2' } });
  await waitFor(() => expect(screen.getByLabelText('Target role')).toHaveValue('2'));
  expect(screen.getByTestId('chosen-role')).toHaveTextContent('2');
  expect(api.get).toHaveBeenCalledWith('/skill-gaps?role_id=2');
});

it('adds catalog skills to a project, suggests a role, normalizes URLs, and shows clickable links', async () => {
  let saved = [];
  vi.spyOn(api, 'get').mockImplementation(async (path) => {
    if (path === '/students/projects') return saved;
    if (path === '/skills') return [{ id: 7, name: 'React', category: 'Frontend' }, { id: 8, name: 'Flask', category: 'Backend' }];
    throw new Error(`Unexpected ${path}`);
  });
  vi.spyOn(api, 'post').mockImplementation(async (path, payload) => { saved = [{ id: 10, ...payload }]; return saved[0]; });
  withAuth(<PortfolioPage />);
  const techInput = await screen.findByRole('combobox', { name: 'Technologies' });
  fireEvent.change(techInput, { target: { value: 'Rea' } });
  fireEvent.click(await screen.findByRole('option', { name: /React/ }));
  expect(screen.getByRole('status')).toHaveTextContent('Frontend Developer');
  expect(screen.getByLabelText('Your role')).toHaveValue('Frontend Developer');
  fireEvent.change(screen.getByLabelText('Project title'), { target: { value: 'Study planner' } });
  fireEvent.change(screen.getByLabelText('Project URL'), { target: { value: 'study.example.com' } });
  fireEvent.change(screen.getByLabelText('GitHub URL'), { target: { value: 'github.com/varun/study' } });
  fireEvent.click(screen.getByRole('button', { name: /save entry/i }));
  await waitFor(() => expect(api.post).toHaveBeenCalled());
  expect(api.post).toHaveBeenCalledWith('/students/projects', expect.objectContaining({ technologies: 'React', skill_ids: [7], role: 'Frontend Developer', project_url: 'https://study.example.com', github_url: 'https://github.com/varun/study' }));
  expect(await screen.findByRole('link', { name: 'Open project ↗' })).toHaveAttribute('href', 'https://study.example.com');
  expect(screen.getByRole('link', { name: 'View GitHub ↗' })).toHaveAttribute('href', 'https://github.com/varun/study');
});

it('renders a skill passport even when optional collections are absent', async () => {
  vi.spyOn(api, 'get').mockResolvedValue({ student: { full_name: 'Mina Patel' }, skills: [{ skill_id: 1, skill: 'Python', overall_score: 80 }] });
  withAuth(<SkillPassport />);
  expect(await screen.findByRole('heading', { name: 'Digital skill passport' })).toBeInTheDocument();
  expect(await screen.findByText('Mina Patel')).toBeInTheDocument();
  expect(screen.getByText(/Python:/)).toBeInTheDocument();
  expect(screen.getAllByText('Nothing to show yet.').length).toBeGreaterThan(0);
});

it('updates the authenticated display name as soon as the profile is saved', async () => {
  localStorage.setItem(TOKEN_KEY, 'student-token');
  vi.spyOn(api, 'get').mockImplementation(async (path) => path === '/auth/me' ? { id: 4, role: 'STUDENT', full_name: 'Old Name', first_name: 'Old' } : { full_name: 'Old Name' });
  vi.spyOn(api, 'put').mockResolvedValue({ full_name: 'New Name' });
  function DisplayName() { const { displayName } = useAuth(); return <output data-testid="display-name">{displayName}</output>; }
  function TestApp() { return <><DisplayName /><ProfilePage /></>; }
  withAuth(<TestApp />);
  expect(await screen.findByTestId('display-name')).toHaveTextContent('Old Name');
  await waitFor(() => expect(screen.getByLabelText('Full name')).toHaveValue('Old Name'));
  fireEvent.change(screen.getByLabelText('Full name'), { target: { value: 'New Name' } });
  fireEvent.click(screen.getByRole('button', { name: /save profile/i }));
  await waitFor(() => expect(screen.getByTestId('display-name')).toHaveTextContent('New Name'));
});

it('shows a student application progress tracker from the saved application status', async () => {
  vi.spyOn(api, 'get').mockImplementation(async (path) => {
    if (path === '/opportunities') return [];
    if (path === '/applications/mine') return [{ id: 20, opportunity_id: 9, status: 'INTERVIEW', opportunity: { id: 9, title: 'Backend Intern', kind: 'INTERNSHIP', company: { name: 'Northstar Labs' } } }];
    throw new Error(`Unexpected ${path}`);
  });
  withAuth(<StudentOpportunities />);
  expect(await screen.findByText('Backend Intern')).toBeInTheDocument();
  expect(screen.getByLabelText('Application status: Interview')).toBeInTheDocument();
  expect(screen.getAllByText('Interview').length).toBeGreaterThan(0);
});

  it('lets an industry user advance an applicant through the status pipeline', async () => {
  const applicant = { id: 30, status: 'APPLIED', student: { full_name: 'Mina Patel', degree: 'B.Tech', institution: 'North College' }, match: { match_percentage: 78, required_skills: [{ skill_id: 2, skill: 'Python', student_score: 80, required_score: 70 }], skill_gaps: [], relevant_projects: [], evidence: [] } };
  vi.spyOn(api, 'get').mockImplementation(async (path) => {
    if (path === '/industry/summary') return { jobs: 1, internships: 0, applications: 1, shortlisted: 0, offers: 0, rejected: 0 };
    if (path === '/industry/company') return { id: 2, user_id: 5, name: 'Northstar Labs', website: '', description: '', location: 'Chennai' };
    if (path === '/opportunities') return [{ id: 9, title: 'Backend Intern', kind: 'INTERNSHIP', is_active: true }];
    if (path === '/skills') return [{ id: 2, name: 'Python' }];
    if (path === '/opportunities/9/applications') return [applicant];
    throw new Error(`Unexpected ${path}`);
  });
  vi.spyOn(api, 'patch').mockImplementation(async (_path, body) => ({ ...applicant, status: body.status }));
  withAuth(<IndustryWorkspace />);
  fireEvent.click(await screen.findByRole('button', { name: 'View applicants' }));
  const status = await screen.findByLabelText('Update status for Mina Patel');
  fireEvent.change(status, { target: { value: 'REVIEWING' } });
  fireEvent.click(screen.getByRole('button', { name: 'Update' }));
  await waitFor(() => expect(api.patch).toHaveBeenCalledWith('/applications/30/status', { status: 'REVIEWING' }));
    expect(await screen.findByText('Reviewing', { selector: 'strong' })).toBeInTheDocument();
  });

  it('loads industry dashboard metrics and opportunity data from the existing APIs', async () => {
    vi.spyOn(api, 'get').mockImplementation(async (path) => {
      if (path === '/industry/summary') return { jobs: 3, internships: 2, applications: 14, shortlisted: 4 };
      if (path === '/industry/company') return { id: 2, name: 'Northstar Labs', website: '', description: '', location: 'Chennai' };
      if (path === '/opportunities') return [{ id: 9, title: 'Backend Engineer', kind: 'JOB', location: 'Chennai', is_active: true, required_skills: [{ skill_id: 2, skill: 'Python', weight: 2, required_proficiency: 70 }] }];
      if (path === '/skills') return [{ id: 2, name: 'Python' }];
      throw new Error(`Unexpected ${path}`);
    });
    withAuth(<IndustryWorkspace />);
    expect(await screen.findByRole('heading', { name: 'Find the right talent' })).toBeInTheDocument();
    expect(screen.getByText('Active jobs').closest('.industry-metric').querySelector('strong')).toHaveTextContent('3');
    expect(screen.getByText('Active internships').closest('.industry-metric').querySelector('strong')).toHaveTextContent('2');
    expect(screen.getByText('Applications', { selector: '.industry-metric-top span' }).closest('.industry-metric').querySelector('strong')).toHaveTextContent('14');
    expect(screen.getByText('Shortlisted').closest('.industry-metric').querySelector('strong')).toHaveTextContent('4');
    fireEvent.click(await screen.findByRole('button', { name: 'View applicants' }));
    await waitFor(() => expect(api.get).toHaveBeenCalledWith('/opportunities/9/applications'));
  });

  it('creates a posting with selected skill and its weight through the existing API', async () => {
    vi.spyOn(api, 'get').mockImplementation(async (path) => {
      if (path === '/industry/summary') return { jobs: 0, internships: 0, applications: 0, shortlisted: 0 };
      if (path === '/industry/company') return { id: 2, name: 'Northstar Labs', website: '', description: '', location: 'Chennai' };
      if (path === '/opportunities') return [];
      if (path === '/skills') return [{ id: 2, name: 'Python' }, { id: 3, name: 'SQL' }];
      throw new Error(`Unexpected ${path}`);
    });
    vi.spyOn(api, 'post').mockResolvedValue({ id: 10 });
    withAuth(<IndustryWorkspace />);
    fireEvent.change(await screen.findByLabelText('Title'), { target: { value: 'Platform Engineer' } });
    fireEvent.change(screen.getByLabelText('Description'), { target: { value: 'Build reliable backend services' } });
    await waitFor(() => expect(screen.getByRole('button', { name: /add a required skill/i })).toBeEnabled());
    fireEvent.click(screen.getByRole('button', { name: /add a required skill/i }));
    await waitFor(() => expect(screen.getByRole('button', { name: /publish opportunity/i })).toBeEnabled());
    fireEvent.submit(screen.getByRole('button', { name: /publish opportunity/i }).closest('form'));
    await waitFor(() => expect(api.post).toHaveBeenCalledWith('/opportunities', expect.objectContaining({
      title: 'Platform Engineer', kind: 'JOB', deadline: null,
      required_skills: [{ skill_id: 2, required_proficiency: 70, weight: 1 }],
    })));
  });

  it('opens a candidate profile from API data and shortlists using the existing endpoint', async () => {
    const applicant = {
      id: 30, status: 'APPLIED', student: { full_name: 'Mina Patel', degree: 'B.Tech', branch: 'CSE', institution: 'North College', github_url: 'https://github.com/mina' },
      certifications: [{ id: 4, name: 'Cloud Fundamentals' }], experience: [],
      match: { match_percentage: 78, required_skills: [{ skill_id: 2, skill: 'Python', student_score: 80, required_score: 70, gap: 0 }], matching_skills: [{ skill_id: 2, skill: 'Python', gap: 0 }], skill_gaps: [], missing_skills: [], relevant_projects: [{ id: 7, title: 'Course API', github_url: 'https://github.com/mina/api', skills: [{ id: 2, name: 'Python' }] }], evidence: [{ id: 5, skill_id: 2, skill_name: 'Python', evidence_title: 'API project evidence', source_url: 'https://example.com/evidence', verification_status: 'VERIFIED' }] },
    };
    vi.spyOn(api, 'get').mockImplementation(async (path) => {
      if (path === '/industry/summary') return { jobs: 1, internships: 0, applications: 1, shortlisted: 0 };
      if (path === '/industry/company') return { name: 'Northstar Labs' };
      if (path === '/opportunities') return [{ id: 9, title: 'Backend Engineer', kind: 'JOB', is_active: true, required_skills: [] }];
      if (path === '/skills') return [];
      if (path === '/opportunities/9/applications') return [applicant];
      throw new Error(`Unexpected ${path}`);
    });
    vi.spyOn(api, 'post').mockResolvedValue({ ...applicant, status: 'SHORTLISTED' });
    withAuth(<IndustryWorkspace />);
    fireEvent.click(await screen.findByRole('button', { name: 'View applicants' }));
    fireEvent.click(await screen.findByRole('button', { name: 'View profile' }));
    expect(await screen.findByRole('heading', { name: 'Mina Patel' })).toBeInTheDocument();
    expect(screen.getAllByText('78%').length).toBeGreaterThan(0);
    expect(screen.getByText('Course API')).toBeInTheDocument();
    expect(screen.getByText('Cloud Fundamentals')).toBeInTheDocument();
    expect(screen.getByText('API project evidence')).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: /shortlist/i }));
    await waitFor(() => expect(api.post).toHaveBeenCalledWith('/applications/30/shortlist', {}));
  });

  it('provides responsive industry layout rules for tablet and mobile widths', () => {
    const css = readFileSync('src/styles.css', 'utf8');
    expect(css).toContain('.industry-metric-grid{display:grid;grid-template-columns:repeat(4');
    expect(css).toContain('@media(max-width:820px){.industry-dashboard-grid,.industry-lower-grid{grid-template-columns:1fr}');
    expect(css).toContain('@media(max-width:580px){.industry-workspace{gap:13px}');
    expect(css).toContain('.industry-candidate-drawer{width:min(520px,100%)');
  });

it('shows institution level application outcome counts', async () => {
  vi.spyOn(api, 'get').mockResolvedValue({ institution: 'North College', student_count: 4, placement_readiness: 52.5, internship_applications: 3, application_outcomes: { applied: 2, reviewing: 1, shortlisted: 1, interview: 0, offer: 1, rejected: 0 }, common_skill_gaps: [], skill_demand: [], average_skill_scores: [] });
  withAuth(<InstitutionWorkspace />);
  expect(await screen.findByRole('heading', { name: 'Application outcomes' })).toBeInTheDocument();
  expect(screen.getByText('North College')).toBeInTheDocument();
  expect(screen.getByText('Interview', { selector: 'small' }).nextElementSibling).toHaveTextContent('0');
  expect(screen.getAllByText('1').length).toBeGreaterThan(0);
});
