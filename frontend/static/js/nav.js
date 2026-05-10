/**
 * nav.js — Shell UI + sidebar nav compartido
 * Centraliza la navegación de todos los módulos del sistema.
 */

import { logout, renderProfile } from '/static/js/auth.js';
import { initProfileMenu, toggleTheme } from '/static/js/ui.js';
import { toast } from '/static/js/toast.js';

// ── Iconos SVG ────────────────────────────────────────────────────────────────
const I = {
  dashboard:  `<svg xmlns="http://www.w3.org/2000/svg" width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/><rect x="14" y="14" width="7" height="7"/></svg>`,
  maintain:   `<svg xmlns="http://www.w3.org/2000/svg" width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 20h9"/><path d="M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4L16.5 3.5z"/></svg>`,
  workers:    `<svg xmlns="http://www.w3.org/2000/svg" width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>`,
  rrhh:       `<svg xmlns="http://www.w3.org/2000/svg" width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>`,
  nomina:     `<svg xmlns="http://www.w3.org/2000/svg" width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="1" y="4" width="22" height="16" rx="2"/><line x1="1" y1="10" x2="23" y2="10"/></svg>`,
  empresa:    `<svg xmlns="http://www.w3.org/2000/svg" width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/></svg>`,
  contract:   `<svg xmlns="http://www.w3.org/2000/svg" width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/></svg>`,
  process:    `<svg xmlns="http://www.w3.org/2000/svg" width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/></svg>`,
  calc:       `<svg xmlns="http://www.w3.org/2000/svg" width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="4" y="2" width="16" height="20" rx="2"/><line x1="8" y1="6" x2="16" y2="6"/><line x1="16" y1="10" x2="8" y2="10"/><line x1="11" y1="14" x2="8" y2="14"/><line x1="8" y1="18" x2="11" y2="18"/><line x1="13" y1="16" x2="16" y2="13"/><line x1="16" y1="16" x2="13" y2="13"/></svg>`,
  fin:        `<svg xmlns="http://www.w3.org/2000/svg" width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="4.93" y1="4.93" x2="19.07" y2="19.07"/></svg>`,
  loan:       `<svg xmlns="http://www.w3.org/2000/svg" width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="12" y1="1" x2="12" y2="23"/><path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/></svg>`,
  advance:    `<svg xmlns="http://www.w3.org/2000/svg" width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="2" y="5" width="20" height="14" rx="2"/><line x1="2" y1="10" x2="22" y2="10"/></svg>`,
  bulk:       `<svg xmlns="http://www.w3.org/2000/svg" width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="18" height="18" rx="2"/><line x1="3" y1="9" x2="21" y2="9"/><line x1="3" y1="15" x2="21" y2="15"/><line x1="9" y1="9" x2="9" y2="21"/></svg>`,
  params:     `<svg xmlns="http://www.w3.org/2000/svg" width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="4" y1="21" x2="4" y2="14"/><line x1="4" y1="10" x2="4" y2="3"/><line x1="12" y1="21" x2="12" y2="12"/><line x1="12" y1="8" x2="12" y2="3"/><line x1="20" y1="21" x2="20" y2="16"/><line x1="20" y1="12" x2="20" y2="3"/><line x1="1" y1="14" x2="7" y2="14"/><line x1="9" y1="8" x2="15" y2="8"/><line x1="17" y1="16" x2="23" y2="16"/></svg>`,
  catalogues: `<svg xmlns="http://www.w3.org/2000/svg" width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="8" y1="6" x2="21" y2="6"/><line x1="8" y1="12" x2="21" y2="12"/><line x1="8" y1="18" x2="21" y2="18"/><line x1="3" y1="6" x2="3.01" y2="6"/><line x1="3" y1="12" x2="3.01" y2="12"/><line x1="3" y1="18" x2="3.01" y2="18"/></svg>`,
  wrench:     `<svg xmlns="http://www.w3.org/2000/svg" width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z"/></svg>`,
  shield:     `<svg xmlns="http://www.w3.org/2000/svg" width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>`,
  tenant:     `<svg xmlns="http://www.w3.org/2000/svg" width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/></svg>`,
  users:      `<svg xmlns="http://www.w3.org/2000/svg" width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>`,
  group:      `<svg xmlns="http://www.w3.org/2000/svg" width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="9" cy="12" r="3"/><circle cx="17" cy="6" r="3"/><circle cx="17" cy="18" r="3"/><line x1="11.83" y1="13.3" x2="14.17" y2="16.7"/><line x1="11.83" y1="10.7" x2="14.17" y2="7.3"/></svg>`,
};

const CHEVRON = `<svg class="nav-chevron" xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="rgba(255,255,255,0.3)" stroke-width="2.5"><polyline points="6 9 12 15 18 9"/></svg>`;

// ── Definición de grupos ──────────────────────────────────────────────────────
function getGroups(user) {
  const sa = user.role === 'superadmin';
  return [
    { type: 'item', page: 'dashboard', label: 'Dashboard', href: '/app.html', icon: I.dashboard },
    {
      type: 'group', id: 'rrhh', label: 'RRHH', icon: I.rrhh,
      items: [
        { page: 'trabajadores', label: 'Trabajadores', href: '/rrhh/trabajadores.html', icon: I.workers  },
        { page: 'contratos',    label: 'Contratos',    href: '/nomina/contratos.html',  icon: I.contract },
        { page: 'finiquitos',   label: 'Finiquitos',   href: '/nomina/finiquitos.html', icon: I.fin      },
      ],
    },
    {
      type: 'group', id: 'nomina', label: 'Nómina', icon: I.nomina,
      items: [
        { page: 'anticipos',    label: 'Anticipos',       href: '/nomina/anticipos.html',    icon: I.advance },
        { page: 'carga-masiva', label: 'Carga masiva',    href: '/nomina/carga-masiva.html', icon: I.bulk    },
        { page: 'movimientos',  label: 'Proceso mensual', href: '/nomina/movimientos.html',  icon: I.process },
        { page: 'calculo',      label: 'Liquidaciones',   href: '/nomina/calculo.html',      icon: I.calc    },
        { page: 'prestamos',    label: 'Préstamos',       href: '/nomina/prestamos.html',    icon: I.loan    },
      ],
    },
    {
      type: 'group', id: 'mantenedores', label: 'Mantenedores', icon: I.wrench,
      items: [
        { page: 'rrhh-mantenedores', label: 'Mantenedores RRHH', href: '/rrhh/mantenedores.html', icon: I.maintain   },
        { page: 'rrhh-catalogos',    label: 'Catálogos RRHH',    href: '/rrhh/catalogos.html',    icon: I.catalogues },
        { page: 'nomina-catalogos',  label: 'Catálogos Nómina',  href: '/nomina/catalogos.html',  icon: I.catalogues },
        { page: 'empresa',           label: 'Empresa',            href: '/nomina/empresa.html',    icon: I.empresa    },
        { page: 'nomina-parametros', label: 'Parámetros',         href: '/nomina/parametros.html', icon: I.params     },
      ],
    },
    {
      type: 'group', id: 'sistema', label: 'Sistema', icon: I.shield,
      items: [
        ...(sa ? [{ page: 'tenants', label: 'Tenants', href: '/tenants.html', icon: I.tenant }] : []),
        { page: 'users',  label: 'Usuarios', href: '/users.html',  icon: I.users  },
        { page: 'groups', label: 'Grupos',   href: '/groups.html', icon: I.group  },
        { page: 'roles',  label: 'Roles',    href: '/roles.html',  icon: I.shield },
      ],
    },
  ];
}

// ── Nav renderer ──────────────────────────────────────────────────────────────
export function initSidebarNav(user) {
  const nav = document.getElementById('sidebar-nav');
  if (!nav) return;
  const active = document.body.dataset.page || '';
  const groups = getGroups(user);
  let html = '';

  for (const g of groups) {
    if (g.type === 'item') {
      html += `<div class="nav-item ${active === g.page ? 'active' : ''}" data-href="${g.href}">${g.icon}<span>${g.label}</span></div>`;
    } else {
      const hasActive = g.items.some(i => i.page === active);
      html += `<div class="nav-group-header ${hasActive ? 'expanded' : ''}" data-group="${g.id}">${g.icon}<span>${g.label}</span>${CHEVRON}</div>`;
      html += `<div class="nav-sub ${hasActive ? 'open' : ''}" id="nav-group-${g.id}">`;
      for (const item of g.items) {
        html += `<div class="nav-item ${active === item.page ? 'active' : ''}" data-href="${item.href}">${item.icon}<span>${item.label}</span></div>`;
      }
      html += `</div>`;
    }
  }

  nav.innerHTML = html;

  nav.querySelectorAll('.nav-group-header').forEach(h => {
    h.addEventListener('click', () => {
      const sub = document.getElementById(`nav-group-${h.dataset.group}`);
      const open = sub.classList.toggle('open');
      h.classList.toggle('expanded', open);
    });
  });

  nav.querySelectorAll('.nav-item[data-href]').forEach(el => {
    el.addEventListener('click', () => { window.location.href = el.dataset.href; });
  });
}

// ── Shell UI completo (nav + profile + theme + logout) ────────────────────────
export function initShellUI(user) {
  renderProfile(user);
  initProfileMenu();
  initSidebarNav(user);

  function _syncTheme() {
    const dark = document.documentElement.getAttribute('data-theme') === 'dark';
    const label = document.getElementById('theme-label');
    const sun   = document.getElementById('theme-icon-sun');
    const moon  = document.getElementById('theme-icon-moon');
    if (label) label.textContent = dark ? 'Modo claro' : 'Modo oscuro';
    if (sun)   sun.style.display  = dark ? 'none'  : 'block';
    if (moon)  moon.style.display = dark ? 'block' : 'none';
  }
  _syncTheme();

  document.getElementById('theme-toggle-btn')?.addEventListener('click', e => {
    e.stopPropagation(); toggleTheme(); _syncTheme();
  });
  document.getElementById('help-btn')?.addEventListener('click', e => {
    e.stopPropagation();
    document.getElementById('profile-menu')?.classList.remove('open');
    toast.info('Sección de ayuda próximamente disponible.');
  });
  document.getElementById('logout-btn')?.addEventListener('click', e => {
    e.stopPropagation(); logout();
  });
}
