import { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState } from 'react';
import { api, TOKEN_KEY } from '../services/api';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [profileName, setProfileName] = useState('');
  const profileNameVersion = useRef(0);
  const [loading, setLoading] = useState(Boolean(localStorage.getItem(TOKEN_KEY)));

  const logout = useCallback(() => {
    localStorage.removeItem(TOKEN_KEY);
    setUser(null);
    setProfileName('');
    setLoading(false);
  }, []);

  useEffect(() => {
    if (user?.role !== 'STUDENT') { setProfileName(''); return undefined; }
    let active = true;
    const version = profileNameVersion.current;
    api.get('/students/profile').then((profile) => {
      if (active && version === profileNameVersion.current) setProfileName(profile?.full_name || '');
    }).catch(() => { if (active && version === profileNameVersion.current) setProfileName(''); });
    return () => { active = false; };
  }, [user?.id, user?.role]);

  useEffect(() => {
    const handleUnauthorized = () => logout();
    window.addEventListener('skillbridge:unauthorized', handleUnauthorized);
    const token = localStorage.getItem(TOKEN_KEY);
    if (!token) return () => window.removeEventListener('skillbridge:unauthorized', handleUnauthorized);
    api.get('/auth/me')
      .then(setUser)
      .catch(logout)
      .finally(() => setLoading(false));
    return () => window.removeEventListener('skillbridge:unauthorized', handleUnauthorized);
  }, [logout]);

  const acceptSession = (response) => {
    localStorage.setItem(TOKEN_KEY, response.access_token);
    setUser(response.user);
  };
  const login = async (credentials) => acceptSession(await api.post('/auth/login', credentials));
  const register = async (details) => acceptSession(await api.post('/auth/register', { ...details, role: details.role || 'STUDENT' }));

  const updateProfileName = (name) => {
    const cleanName = name || '';
    profileNameVersion.current += 1;
    setProfileName(cleanName);
    setUser((current) => current ? { ...current, full_name: cleanName, first_name: cleanName.split(/\s+/)[0] || current.first_name } : current);
  };
  const displayName = profileName || user?.full_name || user?.first_name || 'Student';
  const value = useMemo(() => ({ user, loading, displayName, updateProfileName, login, register, logout }), [user, loading, displayName, logout]);
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) throw new Error('useAuth must be used within AuthProvider');
  return context;
}
