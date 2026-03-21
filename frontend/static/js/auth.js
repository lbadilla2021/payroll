/**
 * auth.js — Session guard & profile utilities
 *
 * Import on every authenticated page to ensure valid session.
 * On success, resolves with the current user object.
 */

import api from './api.js';

let _currentUser = null;

export async function requireAuth() {
  try {
    _currentUser = await api.get('/auth/me');
    return _currentUser;
  } catch {
    window.location.href = '/login.html';
    throw new Error('Unauthenticated');
  }
}

export function getCurrentUser() { return _currentUser; }

export async function logout() {
  try { await api.post('/auth/logout'); } catch {}
  window.location.href = '/login.html';
}

export function isSuperadmin() { return _currentUser?.role === 'superadmin'; }
export function isAdmin()      { return _currentUser?.role === 'admin'; }

/** Fill sidebar profile section */
export function renderProfile(user) {
  const initials = ((user.first_name?.[0] || '') + (user.last_name?.[0] || '')).toUpperCase();
  const el = document.getElementById('sidebar-avatar');
  if (el) el.textContent = initials;
  const name = document.getElementById('sidebar-name');
  if (name) name.textContent = user.full_name || user.email;
  const role = document.getElementById('sidebar-role');
  if (role) role.textContent = ({ superadmin: 'Superadmin', admin: 'Administrador', viewer: 'Viewer' })[user.role] || user.role;
}
