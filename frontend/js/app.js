const appMessage = document.getElementById('app-message');

async function api(path, options = {}) {
  const res = await window.PayrollSession.fetchWithAuth(path, options);
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    if (res.status === 401) {
      window.PayrollSession.clear();
      window.location.href = '/';
      throw new Error('Sesión expirada');
    }
    throw new Error(data.detail || 'Error de API');
  }
  return data;
}

function showMessage(text, ok = false) {
  appMessage.textContent = text;
  appMessage.style.color = ok ? '#12b76a' : '#b42318';
}

async function bootstrapSession() {
  try {
    await window.PayrollSession.refresh();
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
    await api('/api/auth/logout', { method: 'POST' });
  } catch {}
  window.PayrollSession.clear();
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
