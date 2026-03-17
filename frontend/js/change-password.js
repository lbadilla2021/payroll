const form = document.getElementById('change-form');
const message = document.getElementById('message');

async function getToken() {
  let token = sessionStorage.getItem('access_token');
  if (token) return token;
  const r = await fetch('/api/auth/refresh', { method: 'POST', credentials: 'include' });
  if (!r.ok) throw new Error('Sesión expirada');
  const data = await r.json();
  sessionStorage.setItem('access_token', data.access_token);
  return data.access_token;
}

form.addEventListener('submit', async (event) => {
  event.preventDefault();
  try {
    const token = await getToken();
    const payload = {
      current_password: document.getElementById('current_password').value,
      new_password: document.getElementById('new_password').value,
      new_password_confirm: document.getElementById('new_password_confirm').value,
    };
    const res = await fetch('/api/auth/change-password', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
      body: JSON.stringify(payload),
      credentials: 'include',
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || 'Error');
    message.style.color = '#12b76a';
    message.textContent = data.message;
    sessionStorage.removeItem('access_token');
  } catch (e) {
    message.style.color = '#b42318';
    message.textContent = e.message;
  }
});
