let token = sessionStorage.getItem('access_token');
const appMessage = document.getElementById('app-message');
const meEl = document.getElementById('me');
const tenantSelect = document.getElementById('tenant-select');
const profileTrigger = document.getElementById('profile-trigger');
const profileMenu = document.getElementById('profile-menu');
const profileInitial = document.getElementById('profile-initial');
const profileEmail = document.getElementById('profile-email');
const profileName = document.getElementById('profile-name');
const profileMenuInitial = document.getElementById('profile-menu-initial');
const profileTriggerName = document.getElementById('profile-trigger-name');
const themeToggle = document.getElementById('theme-toggle');

async function ensureSession() {
  if (token) return;
  const res = await fetch('/api/auth/refresh', { method: 'POST', credentials: 'include' });
  if (!res.ok) {
    window.location.href = '/';
    return;
  }
  const data = await res.json();
  token = data.access_token;
  sessionStorage.setItem('access_token', token);
}

async function api(path, options = {}) {
  await ensureSession();
  const response = await fetch(path, {
    ...options,
    credentials: 'include',
    headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}`, ...(options.headers || {}) },
  });
  if (response.status === 401) {
    const rf = await fetch('/api/auth/refresh', { method: 'POST', credentials: 'include' });
    if (!rf.ok) {
      sessionStorage.removeItem('access_token');
      window.location.href = '/';
      throw new Error('Sesión expirada');
    }
    const session = await rf.json();
    token = session.access_token;
    sessionStorage.setItem('access_token', token);
    return api(path, options);
  }
  const data = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(data.detail || 'Error de API');
  return data;
}

function showMessage(text, isError = true) {
  appMessage.style.color = isError ? '#b42318' : '#12b76a';
  appMessage.textContent = text;
}

function getInitial(fullName, email) {
  if (fullName?.trim()) return fullName.trim()[0].toUpperCase();
  if (email?.trim()) return email.trim()[0].toUpperCase();
  return 'U';
}

function applyTheme(theme) {
  const darkEnabled = theme === 'dark';
  document.body.classList.toggle('dark', darkEnabled);
  themeToggle.checked = darkEnabled;
  localStorage.setItem('theme', darkEnabled ? 'dark' : 'light');
}

function initTheme() {
  const theme = localStorage.getItem('theme') || 'light';
  applyTheme(theme);
}

async function loadMe() {
  const me = await api('/api/auth/me');
  if (me.role !== 'superadmin') {
    window.location.href = '/';
    return;
  }

  // Requerimiento: no mostrar email en la esquina superior derecha
  meEl.textContent = me.full_name || 'Super Admin';

  profileEmail.textContent = me.email;
  profileName.textContent = me.full_name || 'Usuario';
  profileTriggerName.textContent = me.full_name || 'Usuario';
  const initial = getInitial(me.full_name, me.email);
  profileInitial.textContent = initial;
  profileMenuInitial.textContent = initial;
}

async function loadTenants() {
  const tenants = await api('/api/admin/tenants');
  tenantSelect.innerHTML = tenants.map((tenant) => `<option value="${tenant.id}">${tenant.name} (${tenant.code})</option>`).join('');
}

document.getElementById('tenant-form').addEventListener('submit', async (event) => {
  event.preventDefault();
  try {
    await api('/api/admin/tenants', {
      method: 'POST',
      body: JSON.stringify({ name: document.getElementById('tenant-name').value, code: document.getElementById('tenant-code').value }),
    });
    showMessage('Tenant creado correctamente.', false);
    event.target.reset();
    await loadTenants();
  } catch (error) {
    showMessage(error.message);
  }
});

document.getElementById('user-form').addEventListener('submit', async (event) => {
  event.preventDefault();
  try {
    await api('/api/admin/users', {
      method: 'POST',
      body: JSON.stringify({
        full_name: document.getElementById('user-full-name').value,
        email: document.getElementById('user-email').value,
        password: document.getElementById('user-password').value,
        tenant_id: Number(tenantSelect.value),
        role: 'tenant_admin',
      }),
    });
    showMessage('Usuario tenant_admin creado correctamente.', false);
    event.target.reset();
  } catch (error) {
    showMessage(error.message);
  }
});

document.querySelectorAll('.menu-item[data-view]').forEach((button) => {
  button.addEventListener('click', async () => {
    document.querySelectorAll('.menu-item[data-view]').forEach((item) => item.classList.remove('active'));
    button.classList.add('active');

    const view = button.dataset.view;
    document.getElementById('view-title').textContent = view === 'tenants' ? 'Crear tenant' : 'Crear usuario tenant';
    document.getElementById('view-tenants').classList.toggle('hidden', view !== 'tenants');
    document.getElementById('view-users').classList.toggle('hidden', view !== 'users');

    if (view === 'users') {
      await loadTenants();
    }
  });
});

profileTrigger.addEventListener('click', (event) => {
  event.stopPropagation();
  profileMenu.classList.toggle('hidden');
});

document.addEventListener('click', (event) => {
  if (!profileMenu.classList.contains('hidden') && !profileMenu.contains(event.target) && !profileTrigger.contains(event.target)) {
    profileMenu.classList.add('hidden');
  }
});

themeToggle.addEventListener('change', () => {
  applyTheme(themeToggle.checked ? 'dark' : 'light');
});

document.getElementById('profile-config').addEventListener('click', () => {
  showMessage('Configuración estará disponible próximamente.', false);
  profileMenu.classList.add('hidden');
});

document.getElementById('profile-help').addEventListener('click', () => {
  showMessage('Ayuda: contacta al equipo de plataforma de remuneraciones.', false);
  profileMenu.classList.add('hidden');
});

document.getElementById('profile-password').addEventListener('click', () => {
  window.location.href = '/change-password.html';
});

document.getElementById('logout').addEventListener('click', async () => {
  try {
    await api('/api/auth/logout', { method: 'POST', body: JSON.stringify({ all_sessions: false }) });
  } catch {}
  sessionStorage.removeItem('access_token');
  window.location.href = '/';
});

initTheme();
loadMe();
loadTenants().catch(() => null);
