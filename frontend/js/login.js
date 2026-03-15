const form = document.getElementById('login-form');
const message = document.getElementById('message');

form.addEventListener('submit', async (event) => {
  event.preventDefault();
  message.textContent = '';

  const email = document.getElementById('email').value;
  const password = document.getElementById('password').value;

  const response = await fetch('/api/auth/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password }),
  });

  const data = await response.json();

  if (!response.ok) {
    message.textContent = data.detail || 'Error de login';
    return;
  }

  localStorage.setItem('token', data.access_token);
  window.location.href = '/app.html';
});
