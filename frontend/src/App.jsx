import { Navigate, NavLink, Outlet, Route, Routes, useLocation, useNavigate } from 'react-router-dom';
import { useState } from 'react';
import { useAuth } from './context/AuthContext';
import ProtectedRoute from './components/ProtectedRoute';
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
];

function AppShell() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [targetRoleId, setTargetRoleId] = useState(() => localStorage.getItem('skillbridge_target_role') || '');
  const updateTarget = (value) => {
    setTargetRoleId(value);
    if (value) localStorage.setItem('skillbridge_target_role', value);
  };
  const activePage = navigation.find((item) => item.to === location.pathname)?.label || 'Student workspace';
  return <div className="app-frame">
    <aside className="sidebar">
      <NavLink to="/app" className="brand"><span className="brand-mark">S</span><span>skillbridge<span className="brand-dot">.</span><small>STUDENT WORKSPACE</small></span></NavLink>
      <div className="nav-caption">WORKSPACE</div>
      <nav aria-label="Main navigation" className="main-nav">{navigation.map((item) => <NavLink key={item.to} to={item.to} end={item.end} className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}><span className="nav-icon">{item.icon}</span>{item.label}{item.to === '/app/ai' && <span className="nav-new">NEW</span>}</NavLink>)}</nav>
      <div className="sidebar-bottom"><div className="local-note"><span className="local-pulse" />Private workspace<small>Your learning data, in one place</small></div><button className="nav-link logout-link" onClick={() => { logout(); navigate('/login'); }}><span className="nav-icon">↪</span>Sign out</button></div>
    </aside>
    <main className="main-area">
      <header className="topbar"><button className="mobile-brand" onClick={() => navigate('/app')} aria-label="Go to overview">S</button><div><div className="eyebrow">STUDENT WORKSPACE</div><h1>{activePage}</h1></div><div className="topbar-user"><div className="avatar">{(user?.first_name || 'S').slice(0, 1).toUpperCase()}</div><span><strong>{user?.full_name || user?.first_name || 'Student'}</strong><small>Student account</small></span></div></header>
      <div className="content-area"><Outlet context={{ targetRoleId, setTargetRoleId: updateTarget }} /></div>
    </main>
    <nav className="mobile-nav" aria-label="Mobile navigation">{navigation.slice(0, 5).map((item) => <NavLink key={item.to} to={item.to} end={item.end} aria-label={item.label} className={({ isActive }) => isActive ? 'active' : ''}><span>{item.icon}</span><small>{item.label.split(' ')[0]}</small></NavLink>)}</nav>
  </div>;
}

function App() {
  const { user, loading } = useAuth();
  if (loading) return <div className="page-loading"><span className="spinner" />Loading SkillBridge…</div>;
  return <Routes>
    <Route path="/" element={<Navigate to={user ? '/app' : '/login'} replace />} />
    <Route path="/login" element={user ? <Navigate to="/app" replace /> : <AuthPage mode="login" />} />
    <Route path="/register" element={user ? <Navigate to="/app" replace /> : <AuthPage mode="register" />} />
    <Route element={<ProtectedRoute />}><Route path="/app" element={<AppShell />}>
      <Route index element={<DashboardPage />} /><Route path="profile" element={<ProfilePage />} />
      <Route path="skills" element={<SkillsPage />} /><Route path="assessments" element={<AssessmentsPage />} />
      <Route path="roles" element={<RolesPage />} /><Route path="recommendations" element={<RecommendationsPage />} />
      <Route path="ai" element={<AIStudioPage />} /><Route path="portfolio" element={<PortfolioPage />} />
    </Route></Route>
    <Route path="*" element={<Navigate to={user ? '/app' : '/login'} replace />} />
  </Routes>;
}

export default App;
