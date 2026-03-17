const form = document.getElementById('reset-form');
const message = document.getElementById('message');
const params = new URLSearchParams(window.location.search);
const tokenParam = params.get('token');
if (tokenParam) document.getElementById('token').value = tokenParam;

form.addEventListener('submit', async (event) => {
  event.preventDefault();
  const newPassword = document.getElementById('new_password').value;
  const confirm = document.getElementById('new_password_confirm').value;
  if (newPassword !== confirm) {
    message.textContent = 'Las contraseñas no coinciden.';
    return;
  }

  const payload = { token: document.getElementById('token').value.trim(), new_password: newPassword, new_password_confirm: confirm };
  const response = await fetch('/api/auth/reset-password', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  const data = await response.json().catch(() => ({}));
  message.style.color = response.ok ? '#12b76a' : '#b42318';
  message.textContent = data.message || data.detail || 'No fue posible procesar la solicitud';
});
