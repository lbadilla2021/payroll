const form = document.getElementById('login-form');
const message = document.getElementById('message');

async function safeParseJson(response) {
  const contentType = response.headers.get('content-type') || '';
  if (!contentType.includes('application/json')) {
    return {};
  }
  return response.json().catch(() => ({}));
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
      message.textContent = data.detail || 'No fue posible autenticar. Revisa backend/API.';
      return;
    }

    localStorage.setItem('token', data.access_token);
    window.location.href = '/app.html';
  } catch {
    message.textContent = 'Error de conexión con el servidor.';
  }
});
