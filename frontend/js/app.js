const token = localStorage.getItem('token');
if (!token) {
  window.location.href = '/';
}

const appMessage = document.getElementById('app-message');
const meEl = document.getElementById('me');
const tenantSelect = document.getElementById('tenant-select');

const headers = {
  'Content-Type': 'application/json',
  Authorization: `Bearer ${token}`,
};

function showMessage(text, isError = true) {
  appMessage.style.color = isError ? '#b42318' : '#067647';
  appMessage.textContent = text;
}

async function api(path, options = {}) {
  const response = await fetch(path, {
    ...options,
    headers: { ...headers, ...(options.headers || {}) },
  });

  const data = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(data.detail || 'Error de API');
  return data;
}

async function loadMe() {
  try {
    const me = await api('/api/auth/me');
    if (me.role !== 'superadmin') {
      localStorage.removeItem('token');
      window.location.href = '/';
      return;
    }
    meEl.textContent = `${me.full_name} (${me.email})`;
  } catch {
    localStorage.removeItem('token');
    window.location.href = '/';
  }
}

async function loadTenants() {
  const tenants = await api('/api/admin/tenants');
  tenantSelect.innerHTML = tenants
    .map((tenant) => `<option value="${tenant.id}">${tenant.name} (${tenant.code})</option>`)
    .join('');
}

document.getElementById('tenant-form').addEventListener('submit', async (event) => {
  event.preventDefault();
  try {
    const name = document.getElementById('tenant-name').value;
    const code = document.getElementById('tenant-code').value;
    await api('/api/admin/tenants', {
      method: 'POST',
      body: JSON.stringify({ name, code }),
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
    const full_name = document.getElementById('user-full-name').value;
    const email = document.getElementById('user-email').value;
    const password = document.getElementById('user-password').value;
    const tenant_id = Number(tenantSelect.value);

    await api('/api/admin/users', {
      method: 'POST',
      body: JSON.stringify({ full_name, email, password, tenant_id, role: 'tenant_admin' }),
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

document.getElementById('logout').addEventListener('click', () => {
  localStorage.removeItem('token');
  window.location.href = '/';
});

loadMe();
loadTenants().catch(() => null);
