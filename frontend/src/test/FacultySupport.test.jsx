import { beforeEach, describe, expect, it, vi } from 'vitest';
import { fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { api } from '../services/api';
import { PortfolioPage } from '../pages/WorkspacePages';
import { FacultyDashboard } from '../pages/FacultyDashboard';
import { StudentMentorship } from '../pages/StudentMentorship';
import { SkillPassport, FacultyWorkspace } from '../pages/AdditionalPages';

beforeEach(() => { vi.restoreAllMocks(); });
const project = { id: 11, title: 'Course API', description: 'A student course API', role: 'Backend Developer', technologies: 'Flask, Custom Tool', github_url: 'https://github.com/test/api', project_url: '', start_date: '2026-09-01', end_date: '2026-09-20', completion_status: 'COMPLETED', verification_status: 'APPROVED', skills: [{ id: 2, name: 'Flask' }] };

it('edits an existing project while preserving dates, role, catalog skills and custom technologies', async () => {
  let projects = [project];
  vi.spyOn(api, 'get').mockImplementation(async path => {
    if (path === '/skills') return [{ id: 2, name: 'Flask' }];
    if (path === '/students/projects') return projects;
    throw new Error(path);
  });
  const post = vi.spyOn(api, 'post');
  vi.spyOn(api, 'put').mockImplementation(async (_path, payload) => { projects = [{ ...project, ...payload, verification_status: 'PENDING' }]; return projects[0]; });
  render(<MemoryRouter><PortfolioPage /></MemoryRouter>);
  fireEvent.click(await screen.findByRole('button', { name: 'Edit Course API' }));
  expect(screen.getByLabelText('Project title')).toHaveValue('Course API');
  expect(screen.getByLabelText('Start date')).toHaveValue('2026-09-01');
  expect(screen.getByLabelText('End date')).toHaveValue('2026-09-20');
  expect(screen.getByLabelText('Your role')).toHaveValue('Backend Developer');
  expect(screen.getByRole('button', { name: 'Remove Custom Tool' })).toBeInTheDocument();
  fireEvent.change(screen.getByLabelText('Project title'), { target: { value: 'Improved API' } });
  fireEvent.click(screen.getByRole('button', { name: /save changes/i }));
  await waitFor(() => expect(api.put).toHaveBeenCalledWith('/students/projects/11', expect.objectContaining({ title: 'Improved API', start_date: '2026-09-01', end_date: '2026-09-20', role: 'Backend Developer', skill_ids: [2], technologies: 'Flask, Custom Tool', completion_status: 'COMPLETED' })));
  expect(post).not.toHaveBeenCalled();
  expect(await screen.findByRole('button', { name: 'Edit Improved API' })).toBeInTheDocument();
  expect(await screen.findByText(/Awaiting faculty review/)).toBeInTheDocument();
});

it('cancels editing without writing the project', async () => {
  vi.spyOn(api, 'get').mockImplementation(async path => path === '/skills' ? [] : [project]);
  const put = vi.spyOn(api, 'put');
  render(<MemoryRouter><PortfolioPage /></MemoryRouter>);
  fireEvent.click(await screen.findByRole('button', { name: 'Edit Course API' }));
  fireEvent.change(screen.getByLabelText('Project title'), { target: { value: 'Unsaved title' } });
  fireEvent.click(screen.getByRole('button', { name: 'Cancel editing' }));
  expect(screen.getByLabelText('Project title')).toHaveValue('');
  expect(screen.getByRole('button', { name: /save entry/i })).toBeInTheDocument();
  expect(put).not.toHaveBeenCalled();
});

const review = { id: 5, student_id: 4, student: { id: 4, full_name: 'Mina Patel' }, kind: 'PROJECT', title: 'Course API', status: 'PENDING', updated_at: '2026-09-30T10:00:00', project };
function facultyMock(extra = {}) {
  vi.spyOn(api, 'get').mockImplementation(async path => {
    if (path === '/faculty/summary') return { student_count: 5, selected_students: 3, interview_students: 2, offer_students: 1, pending_verifications: 1, supervised_projects: 0 };
    if (path === '/faculty/students') return [{ id: 4, full_name: 'Mina Patel', branch: 'CSE' }];
    if (path === '/faculty/reviews') return [review];
    if (path === '/faculty/tasks') return [];
    if (path === '/skills') return [{ id: 2, name: 'Flask' }];
    if (path === '/faculty/students/4') return { student: { id: 4, full_name: 'Mina Patel' }, projects: [project], applications: [], gaps: [{ skill_id: 2, skill: 'Flask', current_score: 40, required_score: 70, gap: 30, recommended_topics: ['Flask routing', 'REST APIs'], source: 'Backend Engineer' }] };
    if (path in extra) return extra[path];
    throw new Error(path);
  });
}

describe('faculty workflow', () => {
  it('shows placement counts and sends a faculty decision for the displayed work version', async () => {
    facultyMock();
    vi.spyOn(api, 'post').mockResolvedValue({ ...review, status: 'APPROVED' });
    render(<FacultyDashboard />);
    const notification = await screen.findByRole('region', { name: 'Faculty notifications' });
    await screen.findByRole('button', { name: '✓ Approve' });
    expect(screen.getByText('Students with offers').closest('article')).toHaveTextContent('1');
    expect(screen.getByText('At interview stage').closest('article')).toHaveTextContent('2');
    expect(within(notification).getByRole('link', { name: 'View GitHub ↗' })).toHaveAttribute('href', project.github_url);
    fireEvent.change(screen.getByLabelText('Review feedback for Course API'), { target: { value: 'Inspected source code' } });
    fireEvent.click(screen.getByRole('button', { name: '✓ Approve' }));
    await waitFor(() => expect(api.post).toHaveBeenCalledWith('/faculty/reviews/5/decision', { decision: 'APPROVED', feedback: 'Inspected source code', expected_updated_at: review.updated_at }));
    expect(await screen.findByText(/Faculty endorsement saved/)).toBeInTheDocument();
  });

  it('assigns coursework for a visible skill gap, then supports project supervision', async () => {
    facultyMock();
    vi.spyOn(api, 'post').mockResolvedValue({ id: 7 });
    render(<FacultyDashboard />);
    await screen.findByRole('option', { name: 'Mina Patel · #4' });
    fireEvent.change(screen.getByLabelText('Choose student'), { target: { value: '4' } });
    fireEvent.click(await screen.findByRole('button', { name: 'Assign task for Flask' }));
    expect(screen.getByLabelText('Target skill')).toHaveValue('2');
    expect(screen.getByLabelText('Task instructions')).toHaveValue('Flask routing; REST APIs');
    fireEvent.click(screen.getByRole('button', { name: 'Assign mentorship task' }));
    await waitFor(() => expect(api.post).toHaveBeenCalledWith('/faculty/tasks', expect.objectContaining({ student_id: 4, kind: 'COURSEWORK', skill_id: 2, project_id: null })));
    await screen.findByText(/Task assigned/);
    fireEvent.change(screen.getByLabelText('Task type'), { target: { value: 'PROJECT_SUPERVISION' } });
    fireEvent.change(screen.getByLabelText('Project to supervise'), { target: { value: '11' } });
    fireEvent.change(screen.getByLabelText('Task title'), { target: { value: 'Review project milestones' } });
    fireEvent.change(screen.getByLabelText('Task instructions'), { target: { value: 'Submit architecture and weekly progress' } });
    fireEvent.click(screen.getByRole('button', { name: 'Assign mentorship task' }));
    await waitFor(() => expect(api.post).toHaveBeenCalledWith('/faculty/tasks', expect.objectContaining({ student_id: 4, kind: 'PROJECT_SUPERVISION', project_id: 11 })));
  });

  it('saves only editable faculty profile fields', async () => {
    facultyMock({ '/faculty/profile': { id: 3, user_id: 8, institution: 'Test University', department: 'CSE', designation: 'Professor', interests: 'Research' }, '/faculty/opportunities': [], '/faculty/applications/mine': [] });
    vi.spyOn(api, 'put').mockResolvedValue({ id: 3 });
    render(<FacultyWorkspace />);
    await waitFor(() => expect(screen.getByLabelText('institution')).toHaveValue('Test University'));
    fireEvent.click(screen.getByRole('button', { name: 'Save profile' }));
    await waitFor(() => expect(api.put).toHaveBeenCalledWith('/faculty/profile', { institution: 'Test University', department: 'CSE', designation: 'Professor', interests: 'Research' }));
  });
});

it('lets a student submit mentorship work and read faculty review feedback', async () => {
  const task = { id: 7, status: 'IN_PROGRESS', title: 'Flask practice', description: 'Build a small endpoint', faculty_name: 'Professor John', kind: 'COURSEWORK', skill: 'Flask' };
  vi.spyOn(api, 'get').mockImplementation(async path => path === '/students/mentorship' ? [task] : [{ ...review, status: 'CHANGES_REQUESTED', feedback: 'Add endpoint tests', reviewer: 'Professor John' }]);
  vi.spyOn(api, 'patch').mockImplementation(async (_path, data) => { task.status = data.status; task.submission = data.submission; return task; });
  render(<StudentMentorship />);
  expect(await screen.findByText('Add endpoint tests')).toBeInTheDocument();
  fireEvent.change(screen.getByLabelText('Submission for Flask practice'), { target: { value: 'Built endpoint: https://example.com/work' } });
  fireEvent.click(screen.getByRole('button', { name: 'Submit for faculty review' }));
  await waitFor(() => expect(api.patch).toHaveBeenCalledWith('/students/mentorship/7', { status: 'SUBMITTED', submission: 'Built endpoint: https://example.com/work' }));
  expect(await screen.findByText('Your submission is awaiting faculty review.')).toBeInTheDocument();
});

it('shows a passport endorsement only when faculty approvals exist', async () => {
  const get = vi.spyOn(api, 'get').mockResolvedValue({ student: { full_name: 'Mina' }, skills: [{ skill_id: 2, skill: 'Flask', overall_score: 80, faculty_endorsed: true }], endorsements: { has_endorsements: true, endorsed_items: 1 } });
  const first = render(<SkillPassport />);
  expect(await screen.findByLabelText('Faculty endorsed passport items')).toHaveTextContent('✓ Faculty endorsed');
  expect(screen.getByLabelText('Flask faculty endorsed')).toBeInTheDocument();
  first.unmount();
  get.mockResolvedValue({ student: { full_name: 'Mina' }, skills: [], endorsements: { has_endorsements: false, endorsed_items: 0 } });
  render(<SkillPassport />);
  await screen.findByText('Mina');
  expect(screen.queryByLabelText('Faculty endorsed passport items')).not.toBeInTheDocument();
});

it('resubmits an assessment verification request with a student response', async () => {
  const item = { ...review, kind: 'ASSESSMENT', title: 'Python assessment', status: 'CHANGES_REQUESTED', feedback: 'Explain your revised understanding' };
  vi.spyOn(api, 'get').mockImplementation(async path => path === '/students/mentorship' ? [] : [item]);
  vi.spyOn(api, 'post').mockImplementation(async (_path, payload) => { item.status = 'PENDING'; item.student_response = payload.response; return item; });
  render(<StudentMentorship />);
  fireEvent.change(await screen.findByLabelText('Response for Python assessment'), { target: { value: 'I practiced Python lists and corrected my understanding' } });
  fireEvent.click(screen.getByRole('button', { name: 'Resubmit verification request' }));
  await waitFor(() => expect(api.post).toHaveBeenCalledWith('/students/reviews/5/resubmit', { response: 'I practiced Python lists and corrected my understanding' }));
  expect(await screen.findByText('Verification request sent back to faculty.')).toBeInTheDocument();
});
