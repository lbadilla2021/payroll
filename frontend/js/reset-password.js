const form = document.getElementById('reset-form');
const message = document.getElementById('message');
const params = new URLSearchParams(window.location.search);
const token = params.get('token');

form.addEventListener('submit', async (event) => {
  event.preventDefault();
  const payload = {
    token,
    new_password: document.getElementById('new_password').value,
    new_password_confirm: document.getElementById('new_password_confirm').value,
  };
  const res = await fetch('/api/auth/reset-password', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  const data = await res.json();
  message.style.color = res.ok ? '#12b76a' : '#b42318';
  message.textContent = data.message || data.detail;
});
