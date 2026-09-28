import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react';
import { api, TOKEN_KEY } from '../services/api';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(Boolean(localStorage.getItem(TOKEN_KEY)));

  const logout = useCallback(() => {
    localStorage.removeItem(TOKEN_KEY);
    setUser(null);
    setLoading(false);
  }, []);

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
  const register = async (details) => acceptSession(await api.post('/auth/register', { ...details, role: 'STUDENT' }));

  const value = useMemo(() => ({ user, loading, login, register, logout }), [user, loading, logout]);
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) throw new Error('useAuth must be used within AuthProvider');
  return context;
}
