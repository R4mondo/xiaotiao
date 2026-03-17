const RAW_API_BASE = import.meta.env.VITE_API_BASE_URL || '';
const API_BASE = RAW_API_BASE.replace(/\/api\/v1\/?$/, '');

const TOKEN_KEY = 'zaiyi_token';
const USER_KEY = 'zaiyi_user';

export function getAuthToken() {
  return localStorage.getItem(TOKEN_KEY) || '';
}

export function getAuthUser() {
  const raw = localStorage.getItem(USER_KEY);
  if (!raw) return null;
  try {
    return JSON.parse(raw);
  } catch (_e) {
    return null;
  }
}

export function isAuthed() {
  return Boolean(getAuthToken());
}

export function setAuth(token, user) {
  if (token) {
    localStorage.setItem(TOKEN_KEY, token);
  }
  if (user) {
    localStorage.setItem(USER_KEY, JSON.stringify(user));
  }
}

export function clearAuth() {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(USER_KEY);
}

async function authRequest(endpoint, payload) {
  const res = await fetch(`${API_BASE}${endpoint}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload || {})
  });
  if (!res.ok) {
    let msg = `HTTP ${res.status}`;
    try {
      const data = await res.json();
      msg = data.detail || data.error || msg;
    } catch (_e) {}
    throw new Error(msg);
  }
  return await res.json();
}

export async function login(username, password) {
  const data = await authRequest('/auth/login', { username, password });
  if (data && data.token) {
    setAuth(data.token, data.user);
  }
  return data;
}

export async function register(username, password) {
  const data = await authRequest('/auth/register', { username, password });
  if (data && data.token) {
    setAuth(data.token, data.user);
  }
  return data;
}

export async function logout() {
  const token = getAuthToken();
  if (!token) {
    clearAuth();
    return { ok: true };
  }
  try {
    await fetch(`${API_BASE}/auth/logout`, {
      method: 'POST',
      headers: { Authorization: `Bearer ${token}` }
    });
  } catch (_e) {
    // ignore network errors on logout
  }
  clearAuth();
  return { ok: true };
}
