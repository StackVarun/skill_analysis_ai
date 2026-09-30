import { beforeEach, describe, expect, it, vi } from 'vitest';
import { fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import { IndustryWorkspace } from '../pages/IndustryWorkspace';
import { api, TOKEN_KEY } from '../services/api';

function mockWorkspace(skills = [], applicants = []) {
  vi.spyOn(api, 'get').mockImplementation(async path => {
    if (path === '/industry/summary') return {};
    if (path === '/industry/company') return { name: 'Demo Company' };
    if (path === '/skills') return skills;
    if (path === '/opportunities') return [{ id: 9, title: 'Backend Engineer', kind: 'JOB', is_active: true, required_skills: [{ skill_id: 1, skill: 'Python', required_proficiency: 70, weight: 2 }] }];
    if (path === '/opportunities/9/applications') return applicants;
    throw new Error(path);
  });
}

beforeEach(() => { vi.restoreAllMocks(); localStorage.clear(); });

describe('industry skill entry and applicant ranking', () => {
  it('prevents duplicate required skills and keeps targets attached after removal', async () => {
    mockWorkspace([{ id: 1, name: 'Python' }, { id: 2, name: 'SQL' }, { id: 3, name: 'Flask' }]);
    render(<IndustryWorkspace />);
    const add = await screen.findByRole('button', { name: /add a required skill/i });
    await waitFor(() => expect(add).toBeEnabled());
    fireEvent.click(add); fireEvent.click(add);
    const sql = screen.getByLabelText('Required skill 2');
    expect(within(sql).getByRole('option', { name: 'Python' })).toBeDisabled();
    fireEvent.change(screen.getByLabelText('SQL target score'), { target: { value: '85' } });
    fireEvent.click(screen.getByRole('button', { name: 'Remove Python' }));
    expect(screen.getByLabelText('SQL target score')).toHaveValue(85);
    expect(screen.getByLabelText('Required skill 1')).toHaveValue('2');
    expect(within(screen.getByLabelText('Required skill 1')).getByRole('option', { name: 'Python' })).toBeEnabled();
  });

  it('creates a catalog skill when the catalog is empty and selects it for publishing', async () => {
    mockWorkspace();
    vi.spyOn(api, 'post').mockResolvedValue({ id: 4, name: 'FastAPI' });
    render(<IndustryWorkspace />);
    await screen.findByText('Profile ready');
    fireEvent.change(screen.getByLabelText('New catalog skill'), { target: { value: ' FastAPI ' } });
    fireEvent.click(screen.getByRole('button', { name: 'Add new skill' }));
    expect(await screen.findByLabelText('FastAPI target score')).toHaveValue(70);
    expect(api.post).toHaveBeenCalledWith('/skills', { name: 'FastAPI', category: 'Technical' });
    expect(screen.getByLabelText('Required skill 1')).toHaveValue('4');
    expect(screen.getByRole('button', { name: /publish opportunity/i })).toBeEnabled();
  });

  it('reuses a catalog name without creating or adding a duplicate', async () => {
    mockWorkspace([{ id: 1, name: 'Python' }]);
    const post = vi.spyOn(api, 'post');
    render(<IndustryWorkspace />);
    await screen.findByText('Profile ready');
    for (let i = 0; i < 2; i++) {
      fireEvent.change(screen.getByLabelText('New catalog skill'), { target: { value: 'python' } });
      fireEvent.click(screen.getByRole('button', { name: 'Add new skill' }));
      await waitFor(() => expect(screen.getByLabelText('New catalog skill')).toHaveValue(''));
    }
    expect(post).not.toHaveBeenCalled();
    expect(screen.getAllByLabelText(/Required skill \d/)).toHaveLength(1);
  });

  it('ranks applicants by skill weights and shows company targets', async () => {
    const applicant = (id, full_name, score) => ({ id, status: 'APPLIED', student: { full_name }, match: { match_percentage: score, required_skills: [], skill_gaps: [] } });
    mockWorkspace([], [applicant(1, 'Lower Score', 20), applicant(2, 'Best Score', 90), applicant(3, 'Middle Score', 50)]);
    render(<IndustryWorkspace />);
    fireEvent.click(await screen.findByRole('button', { name: 'View applicants' }));
    await screen.findByText('Rank #1 by skill score');
    const rows = document.querySelectorAll('.industry-applicant-row');
    expect(rows[0]).toHaveTextContent('Best Score');
    expect(rows[1]).toHaveTextContent('Middle Score');
    expect(rows[2]).toHaveTextContent('Lower Score');
    expect(screen.getByLabelText('Company skill requirements')).toHaveTextContent('Python: target 70/100 · weight 2');
  });
});

describe('login API handling', () => {
  it('does not attach a stale bearer token to login or treat invalid credentials as an expired session', async () => {
    localStorage.setItem(TOKEN_KEY, 'old-token');
    const listener = vi.fn();
    window.addEventListener('skillbridge:unauthorized', listener);
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ status: 401, ok: false, json: async () => ({ message: 'Invalid email or password' }) }));
    try {
      await expect(api.post('/auth/login', { email: 'student@test.com', password: 'wrong' })).rejects.toThrow('Invalid email or password');
      expect(fetch.mock.calls[0][1].headers.has('Authorization')).toBe(false);
      expect(listener).not.toHaveBeenCalled();
    } finally { window.removeEventListener('skillbridge:unauthorized', listener); vi.unstubAllGlobals(); }
  });

  it('explains a non-JSON 403 from a wrong server instead of showing only Request failed', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ status: 403, ok: false, json: async () => { throw new Error('HTML response'); } }));
    try {
      await expect(api.post('/auth/login', {})).rejects.toThrow('Check the backend port and Vite proxy target');
    } finally { vi.unstubAllGlobals(); }
  });
});
