/**
 * Auth Guard — included in every protected page
 * 
 * 1. Calls /api/v1/auth/me to verify session
 * 2. Redirects to login if unauthenticated
 * 3. Stores user in window.currentUser
 * 4. Renders sidebar based on role
 * 5. Sets up profile menu and logout
 */

(async function initAuth() {
  try {
    const user = await api.auth.me();
    window.currentUser = user;
    renderSidebar(user);
    renderProfileFooter(user);
    setupProfileMenu();
  } catch (err) {
    window.location.href = '/login.html';
  }
})();

// ── Sidebar navigation config ─────────────────────────────────────────────────
const NAV_CONFIG = {
  superadmin: [
    { label: 'Plataforma', section: true },
    { id: 'tenants', label: 'Organizaciones', icon: `<svg fill="none" stroke="currentColor" stroke-width="1.8" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M3.75 21h16.5M4.5 3h15M5.25 3v18m13.5-18v18M9 6.75h1.5m-1.5 3h1.5m-1.5 3h1.5m3-6H15m-1.5 3H15m-1.5 3H15M9 21v-3.375c0-.621.504-1.125 1.125-1.125h3.75c.621 0 1.125.504 1.125 1.125V21"/></svg>`, href: 'tenants.html' },
    { id: 'users',   label: 'Usuarios',       icon: `<svg fill="none" stroke="currentColor" stroke-width="1.8" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M15 19.128a9.38 9.38 0 002.625.372 9.337 9.337 0 004.121-.952 4.125 4.125 0 00-7.533-2.493M15 19.128v-.003c0-1.113-.285-2.16-.786-3.07M15 19.128v.106A12.318 12.318 0 018.624 21c-2.331 0-4.512-.645-6.374-1.766l-.001-.109a6.375 6.375 0 0111.964-3.07M12 6.375a3.375 3.375 0 11-6.75 0 3.375 3.375 0 016.75 0zm8.25 2.25a2.625 2.625 0 11-5.25 0 2.625 2.625 0 015.25 0z"/></svg>`, href: 'users.html' },
  ],
  admin: [
    { label: 'Gestión', section: true },
    { id: 'users', label: 'Usuarios', icon: `<svg fill="none" stroke="currentColor" stroke-width="1.8" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M15 19.128a9.38 9.38 0 002.625.372 9.337 9.337 0 004.121-.952 4.125 4.125 0 00-7.533-2.493M15 19.128v-.003c0-1.113-.285-2.16-.786-3.07M15 19.128v.106A12.318 12.318 0 018.624 21c-2.331 0-4.512-.645-6.374-1.766l-.001-.109a6.375 6.375 0 0111.964-3.07M12 6.375a3.375 3.375 0 11-6.75 0 3.375 3.375 0 016.75 0zm8.25 2.25a2.625 2.625 0 11-5.25 0 2.625 2.625 0 015.25 0z"/></svg>`, href: 'users.html' },
  ],
  viewer: [
    { label: 'Menú', section: true },
  ],
};

function renderSidebar(user) {
  const nav = document.getElementById('sidebar-nav');
  if (!nav) return;

  const items = NAV_CONFIG[user.role] || NAV_CONFIG.viewer;
  const currentPage = window.location.pathname.split('/').pop();

  nav.innerHTML = items.map(item => {
    if (item.section) return `<div class="nav-section-label">${item.label}</div>`;
    const active = currentPage === item.href ? 'active' : '';
    return `
      <div class="nav-item ${active}" onclick="window.location.href='${item.href}'">
        ${item.icon}
        <span>${item.label}</span>
      </div>`;
  }).join('');
}

function renderProfileFooter(user) {
  const avatar = document.getElementById('profile-avatar');
  const name   = document.getElementById('profile-name');
  const role   = document.getElementById('profile-role');
  if (avatar) avatar.textContent = avatarInitials(user.full_name);
  if (name)   name.textContent   = user.full_name;
  if (role)   role.textContent   = { superadmin: 'Superadmin', admin: 'Administrador', viewer: 'Viewer' }[user.role] || user.role;
}

function setupProfileMenu() {
  const trigger = document.getElementById('profile-trigger');
  const menu    = document.getElementById('profile-menu');
  if (!trigger || !menu) return;

  trigger.addEventListener('click', (e) => {
    e.stopPropagation();
    menu.classList.toggle('open');
  });

  document.addEventListener('click', () => menu.classList.remove('open'));

  document.getElementById('btn-logout')?.addEventListener('click', async () => {
    try {
      await api.auth.logout();
    } finally {
      window.location.href = '/login.html';
    }
  });

  document.getElementById('btn-change-password')?.addEventListener('click', () => {
    menu.classList.remove('open');
    openPanel('panel-change-password');
  });

  document.getElementById('btn-settings')?.addEventListener('click', () => {
    window.location.href = 'settings.html';
  });

  // Change password form in panel
  document.getElementById('form-change-password')?.addEventListener('submit', async (e) => {
    e.preventDefault();
    const btn = e.target.querySelector('[type=submit]');
    setLoading(btn, true);
    try {
      const cp  = document.getElementById('cp-current').value;
      const np  = document.getElementById('cp-new').value;
      const cnp = document.getElementById('cp-confirm').value;
      await api.auth.changePassword(cp, np, cnp);
      toast('Contraseña actualizada. Inicia sesión nuevamente.', 'success');
      setTimeout(() => window.location.href = '/login.html', 1500);
    } catch (err) {
      toast(err.detail || 'Error al cambiar contraseña', 'error');
      setLoading(btn, false);
    }
  });
}
