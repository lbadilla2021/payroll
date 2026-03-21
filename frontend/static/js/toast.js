/**
 * toast.js — Notification system
 * Usage: import { toast } from './toast.js';
 *        toast.success('Tenant created');
 *        toast.error('Something went wrong');
 */

function show(message, type = 'info', duration = 4000) {
  let container = document.getElementById('toast-container');
  if (!container) {
    container = document.createElement('div');
    container.id = 'toast-container';
    document.body.appendChild(container);
  }

  const icons = { success: '✓', error: '✕', warning: '⚠', info: 'ℹ' };
  const el = document.createElement('div');
  el.className = `toast ${type}`;
  el.innerHTML = `
    <span class="toast-icon">${icons[type] || icons.info}</span>
    <span class="toast-message">${message}</span>
  `;
  container.appendChild(el);

  setTimeout(() => {
    el.style.opacity = '0';
    el.style.transform = 'translateX(24px)';
    el.style.transition = 'all 250ms ease';
    setTimeout(() => el.remove(), 260);
  }, duration);
}

export const toast = {
  success: (msg, d) => show(msg, 'success', d),
  error:   (msg, d) => show(msg, 'error',   d),
  warning: (msg, d) => show(msg, 'warning', d),
  info:    (msg, d) => show(msg, 'info',    d),
};
