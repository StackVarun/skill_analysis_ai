const API_BASE = (import.meta.env.VITE_API_BASE_URL || '/api').replace(/\/$/, '');
export const TOKEN_KEY = 'skillbridge_access_token';

export class ApiError extends Error {
  constructor(message, status, payload) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.payload = payload;
  }
}

async function send(path, options = {}) {
  const isAuthRequest = ['/auth/login', '/auth/register'].includes(path);
  const token = isAuthRequest ? null : localStorage.getItem(TOKEN_KEY);
  const headers = new Headers(options.headers || {});
  if (token) headers.set('Authorization', `Bearer ${token}`);
  if (options.body && !(options.body instanceof FormData) && !headers.has('Content-Type')) {
    headers.set('Content-Type', 'application/json');
  }
  let response;
  try {
    response = await fetch(`${API_BASE}${path}`, { ...options, headers });
  } catch {
    throw new ApiError('Unable to reach SkillBridge. Check that the backend is running.', 0);
  }
  if (response.status === 401 && !isAuthRequest) window.dispatchEvent(new CustomEvent('skillbridge:unauthorized'));
  const payload = response.status === 204 ? null : await response.json().catch(() => null);
  if (!response.ok) {
    const message = payload?.message || payload?.error || (response.status === 403 && isAuthRequest
      ? 'The API server refused the login request. Check the backend port and Vite proxy target; on macOS, AirPlay may occupy port 5000. Restart Flask and Vite after changing ports.'
      : `Request failed (${response.status})`);
    throw new ApiError(message, response.status, payload);
  }
  return payload;
}

export const api = {
  get: (path) => send(path),
  post: (path, data) => send(path, { method: 'POST', body: JSON.stringify(data) }),
  put: (path, data) => send(path, { method: 'PUT', body: JSON.stringify(data) }),
  patch: (path, data) => send(path, { method: 'PATCH', body: JSON.stringify(data) }),
  delete: (path) => send(path, { method: 'DELETE' }),
  upload: (path, formData) => send(path, { method: 'POST', body: formData }),
};

export function friendlyError(error) {
  if (error?.payload?.messages) {
    const messages = error.payload.messages;
    return Object.values(messages).flat().join(' ');
  }
  return error?.message || 'Something went wrong. Please try again.';
}
