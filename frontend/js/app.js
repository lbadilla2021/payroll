const appMessage = document.getElementById('app-message');

async function api(path, options = {}) {
  const response = await window.PayrollSession.fetchWithAuth(path, options);
  const data = await response.json().catch(() => ({}));

  if (!response.ok) {
    if (response.status === 401) {
      window.PayrollSession.clearSession();
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

async function logoutAndRedirect() {
  try {
    await window.PayrollSession.fetchWithAuth('/api/auth/logout', {
      method: 'POST',
    });
  } catch {
    // ignore network errors
  }

  window.PayrollSession.clearSession();
  window.location.href = '/';
}

async function bootstrapSession() {
  try {
    await window.PayrollSession.refreshAccessToken();
    const me = await api('/api/auth/me', { method: 'GET' });

    document.getElementById('me').textContent = me.full_name;
    document.getElementById('profile-email').textContent = me.email_normalized;
    document.getElementById('profile-name').textContent = me.full_name;
  } catch {
    window.PayrollSession.clearSession();
    window.location.href = '/';
  }
}

document.getElementById('logout').addEventListener('click', async () => {
  await logoutAndRedirect();
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
