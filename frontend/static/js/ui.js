/**
 * ui.js — Reusable UI primitives
 * Modal, Panel, Overlay, Confirm dialog, theme toggle, pagination
 */

// ── Theme ─────────────────────────────────────────────────────────────────────
export function initTheme() {
  const stored = localStorage.getItem('theme') || 'light';
  document.documentElement.setAttribute('data-theme', stored);
  return stored;
}

export function toggleTheme() {
  const current = document.documentElement.getAttribute('data-theme') || 'light';
  const next = current === 'dark' ? 'light' : 'dark';
  document.documentElement.setAttribute('data-theme', next);
  localStorage.setItem('theme', next);
  const toggle = document.getElementById('theme-toggle');
  if (toggle) toggle.classList.toggle('on', next === 'dark');
  return next;
}

// ── Overlay ───────────────────────────────────────────────────────────────────
let _overlay = null;
function getOverlay() {
  if (!_overlay) {
    _overlay = document.createElement('div');
    _overlay.className = 'overlay';
    _overlay.addEventListener('click', closeAll);
    document.body.appendChild(_overlay);
  }
  return _overlay;
}

export function showOverlay() { getOverlay().classList.add('open'); }
export function hideOverlay() { getOverlay().classList.remove('open'); }

// ── Modal ─────────────────────────────────────────────────────────────────────
export function openModal(id) {
  document.getElementById(id)?.classList.add('open');
  showOverlay();
}
export function closeModal(id) {
  document.getElementById(id)?.classList.remove('open');
  hideOverlay();
}

// ── Panel (slide from right) ──────────────────────────────────────────────────
export function openPanel(id) {
  document.getElementById(id)?.classList.add('open');
  showOverlay();
}
export function closePanel(id) {
  document.getElementById(id)?.classList.remove('open');
  hideOverlay();
}

export function closeAll() {
  document.querySelectorAll('.modal.open, .panel.open').forEach(el => el.classList.remove('open'));
  hideOverlay();
}

// ── Confirm dialog ────────────────────────────────────────────────────────────
export function confirm(message, title = 'Confirmar') {
  return new Promise(resolve => {
    let modal = document.getElementById('__confirm-modal');
    if (!modal) {
      modal = document.createElement('div');
      modal.id = '__confirm-modal';
      modal.className = 'modal';
      modal.innerHTML = `
        <div class="modal-header">
          <span class="modal-title" id="__confirm-title"></span>
        </div>
        <div class="modal-body">
          <p id="__confirm-message" style="color:var(--text-secondary);font-size:14px;"></p>
        </div>
        <div class="modal-footer">
          <button class="btn btn-secondary" id="__confirm-cancel">Cancelar</button>
          <button class="btn btn-danger" id="__confirm-ok">Confirmar</button>
        </div>`;
      document.body.appendChild(modal);
    }
    document.getElementById('__confirm-title').textContent = title;
    document.getElementById('__confirm-message').textContent = message;
    openModal('__confirm-modal');
    const ok = document.getElementById('__confirm-ok');
    const cancel = document.getElementById('__confirm-cancel');
    const handler = (val) => {
      closeModal('__confirm-modal');
      ok.replaceWith(ok.cloneNode(true));
      cancel.replaceWith(cancel.cloneNode(true));
      resolve(val);
    };
    document.getElementById('__confirm-ok').addEventListener('click', () => handler(true), { once: true });
    document.getElementById('__confirm-cancel').addEventListener('click', () => handler(false), { once: true });
  });
}

// ── Loading state ─────────────────────────────────────────────────────────────
export function setLoading(btn, loading) {
  if (loading) {
    btn.dataset.originalText = btn.innerHTML;
    btn.innerHTML = '<span class="spinner" style="width:16px;height:16px;border-width:2px;"></span>';
    btn.disabled = true;
  } else {
    btn.innerHTML = btn.dataset.originalText || btn.innerHTML;
    btn.disabled = false;
  }
}

// ── Pagination ────────────────────────────────────────────────────────────────
export function renderPagination(container, { page, total, size }, onPageChange) {
  const totalPages = Math.ceil(total / size);
  if (totalPages <= 1) { container.innerHTML = ''; return; }
  const start = Math.max(1, page - 2);
  const end = Math.min(totalPages, page + 2);
  let html = `<button class="page-btn" ${page === 1 ? 'disabled' : ''} data-p="${page-1}">‹</button>`;
  if (start > 1) html += `<button class="page-btn" data-p="1">1</button><span style="color:var(--text-muted);padding:0 4px">…</span>`;
  for (let i = start; i <= end; i++) {
    html += `<button class="page-btn ${i === page ? 'active' : ''}" data-p="${i}">${i}</button>`;
  }
  if (end < totalPages) html += `<span style="color:var(--text-muted);padding:0 4px">…</span><button class="page-btn" data-p="${totalPages}">${totalPages}</button>`;
  html += `<button class="page-btn" ${page === totalPages ? 'disabled' : ''} data-p="${page+1}">›</button>`;
  container.innerHTML = html;
  container.querySelectorAll('.page-btn:not([disabled])').forEach(btn => {
    btn.addEventListener('click', () => onPageChange(parseInt(btn.dataset.p)));
  });
}

// ── Profile dropdown toggle ───────────────────────────────────────────────────
export function initProfileMenu() {
  const trigger = document.getElementById('profile-trigger');
  const menu    = document.getElementById('profile-menu');
  if (!trigger || !menu) return;

  trigger.addEventListener('click', (e) => {
    e.preventDefault();
    e.stopPropagation();
    e.stopImmediatePropagation();
    const isOpen = menu.classList.contains('open');
    menu.classList.toggle('open', !isOpen);
  });

  // Close when clicking outside — use capture:false and check target
  document.addEventListener('click', (e) => {
    if (!trigger.contains(e.target) && !menu.contains(e.target)) {
      menu.classList.remove('open');
    }
  });
}

// ── Sidebar nav highlight ─────────────────────────────────────────────────────
export function initNav(currentPage) {
  document.querySelectorAll('.nav-item[data-page]').forEach(el => {
    el.classList.toggle('active', el.dataset.page === currentPage);
    el.addEventListener('click', () => {
      const href = el.dataset.href;
      if (href) window.location.href = href;
    });
  });
}

// ── Escape key closes modals/panels ──────────────────────────────────────────
document.addEventListener('keydown', (e) => { if (e.key === 'Escape') closeAll(); });
