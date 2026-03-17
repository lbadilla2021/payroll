let accessToken = sessionStorage.getItem('access_token');
const appMessage = document.getElementById('app-message');

async function refreshSession() {
  const response = await fetch('/api/auth/refresh', { method: 'POST', credentials: 'include' });
  if (!response.ok) {
    sessionStorage.removeItem('access_token');
    window.location.href = '/';
    throw new Error('Sesión expirada');
  }
  const data = await response.json();
  accessToken = data.access_token;
  sessionStorage.setItem('access_token', accessToken);
}

async function api(path, options = {}) {
  if (!accessToken) await refreshSession();
  const response = await fetch(path, {
    ...options,
    credentials: 'include',
    headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${accessToken}`, ...(options.headers || {}) },
  });
  if (response.status === 401) {
    await refreshSession();
    return api(path, options);
  }
  const data = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(data.detail || 'Error de API');
  return data;
}

function showMessage(text, ok = false) {
  appMessage.textContent = text;
  appMessage.style.color = ok ? '#12b76a' : '#b42318';
}

async function bootstrapSession() {
  try {
    const me = await api('/api/auth/me');
    document.getElementById('me').textContent = me.full_name;
    document.getElementById('profile-email').textContent = me.email_normalized;
    document.getElementById('profile-name').textContent = me.full_name;
  } catch {
    window.location.href = '/';
  }
}

document.getElementById('logout').addEventListener('click', async () => {
  try {
    await api('/api/auth/logout', { method: 'POST', body: JSON.stringify({ all_sessions: false }) });
  } catch {}
  sessionStorage.removeItem('access_token');
  window.location.href = '/';
});

document.getElementById('tenant-form').addEventListener('submit', async (event) => {
  event.preventDefault();
  try {
    await api('/api/admin/tenants', {
      method: 'POST',
      body: JSON.stringify({ name: document.getElementById('tenant-name').value, code: document.getElementById('tenant-code').value }),
    });
    showMessage('Tenant creado.', true);
  } catch (error) {
    showMessage(error.message);
  }
});

bootstrapSession();
