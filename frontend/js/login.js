const form = document.getElementById('login-form');
const message = document.getElementById('message');

function initTheme() {
  const theme = localStorage.getItem('theme') || 'light';
  document.body.classList.toggle('dark', theme === 'dark');
}

async function safeParseJson(response) {
  const contentType = response.headers.get('content-type') || '';
  if (!contentType.includes('application/json')) {
    return {};
  }
  return response.json().catch(() => ({}));
}

function normalizeApiError(detail, status) {
  if (typeof detail === 'string' && detail.trim()) {
    return detail;
  }

  if (Array.isArray(detail) && detail.length > 0) {
    const first = detail[0];
    if (first && typeof first === 'object' && typeof first.msg === 'string') {
      return first.msg;
    }
    return 'Solicitud inválida. Revisa los datos ingresados.';
  }

  if (detail && typeof detail === 'object') {
    if (typeof detail.msg === 'string') {
      return detail.msg;
    }
    return 'Error de validación en la solicitud.';
  }

  return `No fue posible autenticar (HTTP ${status}).`;
}

form.addEventListener('submit', async (event) => {
  event.preventDefault();
  message.textContent = '';

  const email = document.getElementById('email').value;
  const password = document.getElementById('password').value;

  try {
    const response = await fetch('/api/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password }),
    });

    const data = await safeParseJson(response);

    if (!response.ok) {
      message.textContent = normalizeApiError(data.detail, response.status);
      return;
    }

    localStorage.setItem('token', data.access_token);
    window.location.href = '/app.html';
  } catch {
    message.textContent = 'Error de conexión con el servidor.';
  }
});

initTheme();
