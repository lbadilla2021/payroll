/**
 * api.js — Centralized HTTP client
 *
 * - Reads CSRF token from cookie → X-CSRF-Token header on mutations
 * - On 401: attempts refresh, retries once, else redirect to login
 * - credentials: 'include' on every request (cookies)
 */

const API_BASE = '/api/v1';

function getCookie(name) {
  const m = document.cookie.match(new RegExp('(?:^|; )' + name + '=([^;]*)'));
  return m ? decodeURIComponent(m[1]) : null;
}

let _isRefreshing = false;
let _refreshQueue = [];

async function _doRefresh() {
  try {
    const r = await fetch(`${API_BASE}/auth/refresh`, { method: 'POST', credentials: 'include' });
    return r.ok;
  } catch { return false; }
}

async function request(method, path, body, options = {}) {
  const headers = { ...(options.headers || {}) };
  if (body && !(body instanceof FormData)) headers['Content-Type'] = 'application/json';
  if (!['GET','HEAD','OPTIONS'].includes(method.toUpperCase())) {
    const csrf = getCookie('csrf_token');
    if (csrf) headers['X-CSRF-Token'] = csrf;
  }

  const cfg = { method: method.toUpperCase(), headers, credentials: 'include' };
  if (body) cfg.body = (body instanceof FormData) ? body : JSON.stringify(body);

  let res = await fetch(`${API_BASE}${path}`, cfg);

  if (res.status === 401 && !options._retry) {
    if (!_isRefreshing) {
      _isRefreshing = true;
      const ok = await _doRefresh();
      _isRefreshing = false;
      _refreshQueue.forEach(fn => fn(ok));
      _refreshQueue = [];
      if (!ok) { window.location.href = '/login.html'; throw new Error('Session expired'); }
    } else {
      await new Promise(fn => _refreshQueue.push(fn));
    }
    return request(method, path, body, { ...options, _retry: true });
  }

  if (!res.ok) {
    let detail = `HTTP ${res.status}`;
    try { const e = await res.json(); detail = e.detail || detail; } catch {}
    const err = new Error(detail); err.status = res.status; throw err;
  }
  if (res.status === 204) return null;
  return res.json();
}

export const api = {
  get:    (p, o)    => request('GET',    p, null, o),
  post:   (p, b, o) => request('POST',   p, b,    o),
  patch:  (p, b, o) => request('PATCH',  p, b,    o),
  delete: (p, o)    => request('DELETE', p, null, o),
};
export default api;
