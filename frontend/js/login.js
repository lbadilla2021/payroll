const form = document.getElementById('login-form');
const message = document.getElementById('message');

form.addEventListener('submit', async (event) => {
  event.preventDefault();
  message.textContent = '';
  const payload = {
    tenant_code: document.getElementById('tenant_code').value || null,
    email: document.getElementById('email').value,
    password: document.getElementById('password').value,
  };

  const response = await fetch('/api/auth/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
    body: JSON.stringify(payload),
  });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    message.textContent = 'No fue posible autenticar con esos datos.';
    return;
  }
  sessionStorage.setItem('access_token', data.access_token);
  window.location.href = '/app.html';
});
