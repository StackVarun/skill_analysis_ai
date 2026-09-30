import { Navigate, NavLink, Outlet, Route, Routes, useLocation, useNavigate } from 'react-router-dom';
import { useEffect, useState } from 'react';
import { useAuth } from './context/AuthContext';
import { api } from './services/api';
import ProtectedRoute from './components/ProtectedRoute';
import { StudentOpportunities, IndustryWorkspace } from './pages/OpportunityPages';
import { StudentMentorship } from './pages/StudentMentorship';
import { FacultyWorkspace, InstitutionWorkspace, SkillPassport } from './pages/AdditionalPages';
import AuthPage from './pages/AuthPage';
import { DashboardPage, ProfilePage, SkillsPage, AssessmentsPage, RolesPage, RecommendationsPage, AIStudioPage, PortfolioPage } from './pages/WorkspacePages';

const navigation = [
  { to: '/app', label: 'Overview', icon: '⌂', end: true },
  { to: '/app/profile', label: 'My profile', icon: '◎' },
  { to: '/app/skills', label: 'Skills & evidence', icon: '✳' },
  { to: '/app/assessments', label: 'Assessments', icon: '▤' },
  { to: '/app/roles', label: 'Role matching', icon: '◈' },
  { to: '/app/recommendations', label: 'Recommendations', icon: '✧' },
  { to: '/app/ai', label: 'AI studio', icon: '✦' },
  { to: '/app/portfolio', label: 'Portfolio', icon: '▣' },
  { to: '/app/opportunities', label: 'Opportunities', icon: '↗' },
  { to: '/app/passport', label: 'Skill passport', icon: '◉' },
  { to: '/app/mentorship', label: 'Mentorship & reviews', icon: '♧' },
];

function AppShell() {
  const { user, logout, displayName } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [targetRoleId, setTargetRoleId] = useState(() => localStorage.getItem('skillbridge_target_role') || '');
  const [roles, setRoles] = useState([]);
  useEffect(() => {
    if (user?.role !== 'STUDENT') return;
    let active = true;
    api.get('/roles').then((result) => { if (active) setRoles(Array.isArray(result) ? result : []); }).catch(() => { if (active) setRoles([]); });
    return () => { active = false; };
  }, [user?.role]);
  const updateTarget = (value) => {
    setTargetRoleId(value);
    if (value) localStorage.setItem('skillbridge_target_role', value);
  };
  const menu = user?.role === 'STUDENT' ? navigation : [{to:'/app',label:user?.role === 'INDUSTRY' ? 'Industry' : user?.role === 'ACADEMICIAN' ? 'Academician' : 'Institution',icon:'◈',end:true}];
  const activePage = menu.find((item) => item.to === location.pathname)?.label || 'Student workspace';
  return <div className="app-frame">
    <aside className="sidebar">
      <NavLink to="/app" className="brand"><span className="brand-mark">S</span><span>skillbridge<span className="brand-dot">.</span><small>{user?.role || 'WORKSPACE'} WORKSPACE</small></span></NavLink>
      <div className="nav-caption">WORKSPACE</div>
      <nav aria-label="Main navigation" className="main-nav">{menu.map((item) => <NavLink key={item.to} to={item.to} end={item.end} className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}><span className="nav-icon">{item.icon}</span>{item.label}{item.to === '/app/ai' && <span className="nav-new">NEW</span>}</NavLink>)}</nav>
      <div className="sidebar-bottom"><div className="local-note"><span className="local-pulse" />Private workspace<small>Your learning data, in one place</small></div><button className="nav-link logout-link" onClick={() => { logout(); navigate('/login'); }}><span className="nav-icon">↪</span>Sign out</button></div>
    </aside>
    <main className="main-area">
      <header className="topbar"><button className="mobile-brand" onClick={() => navigate('/app')} aria-label="Go to overview">S</button><div><div className="eyebrow">{user?.role} WORKSPACE</div><h1>{activePage}</h1></div>{user?.role === 'STUDENT' && <label className="topbar-role-picker">Target role<select aria-label="Workspace target role" value={targetRoleId} onChange={(event) => updateTarget(event.target.value)}><option value="">Choose a role</option>{roles.map((role) => <option key={role.id} value={role.id}>{role.name}</option>)}</select></label>}<div className="topbar-user"><div className="avatar">{(displayName || 'S').slice(0, 1).toUpperCase()}</div><span><strong>{displayName}</strong><small>{user?.role} account</small></span></div></header>
      <div className="content-area"><Outlet context={{ targetRoleId, setTargetRoleId: updateTarget }} /></div>
    </main>
    <nav className="mobile-nav" aria-label="Mobile navigation">{menu.slice(0, 5).map((item) => <NavLink key={item.to} to={item.to} end={item.end} aria-label={item.label} className={({ isActive }) => isActive ? 'active' : ''}><span>{item.icon}</span><small>{item.label.split(' ')[0]}</small></NavLink>)}</nav>
  </div>;
}

function RoleHome({role}) { return role === 'INDUSTRY' ? <IndustryWorkspace/> : role === 'ACADEMICIAN' ? <FacultyWorkspace/> : role === 'INSTITUTION' ? <InstitutionWorkspace/> : <DashboardPage/>; }

function App() {
  const { user, loading } = useAuth();
  if (loading) return <div className="page-loading"><span className="spinner" />Loading SkillBridge…</div>;
  return <Routes>
    <Route path="/" element={<Navigate to={user ? '/app' : '/login'} replace />} />
    <Route path="/login" element={user ? <Navigate to="/app" replace /> : <AuthPage mode="login" />} />
    <Route path="/register" element={user ? <Navigate to="/app" replace /> : <AuthPage mode="register" />} />
    <Route element={<ProtectedRoute />}><Route path="/app" element={<AppShell />}>
      <Route index element={<RoleHome role={user?.role}/>} /><Route path="profile" element={user?.role === 'STUDENT' ? <ProfilePage/> : <Navigate to="/app"/>} />
      <Route path="skills" element={user?.role === 'STUDENT' ? <SkillsPage/> : <Navigate to="/app"/>} /><Route path="assessments" element={user?.role === 'STUDENT' ? <AssessmentsPage/> : <Navigate to="/app"/>} />
      <Route path="roles" element={user?.role === 'STUDENT' ? <RolesPage/> : <Navigate to="/app"/>} /><Route path="recommendations" element={user?.role === 'STUDENT' ? <RecommendationsPage/> : <Navigate to="/app"/>} />
      <Route path="ai" element={user?.role === 'STUDENT' ? <AIStudioPage/> : <Navigate to="/app"/>} /><Route path="portfolio" element={user?.role === 'STUDENT' ? <PortfolioPage/> : <Navigate to="/app"/>} />
      <Route path="opportunities" element={user?.role === 'STUDENT' ? <StudentOpportunities/> : <Navigate to="/app"/>} /><Route path="passport" element={user?.role === 'STUDENT' ? <SkillPassport/> : <Navigate to="/app"/>} />
      <Route path="mentorship" element={user?.role === 'STUDENT' ? <StudentMentorship/> : <Navigate to="/app"/>} />
    </Route></Route>
    <Route path="*" element={<Navigate to={user ? '/app' : '/login'} replace />} />
  </Routes>;
}

export default App;
