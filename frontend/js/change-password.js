const form = document.getElementById('change-form');
const message = document.getElementById('message');

async function api(path, options = {}) {
  const res = await window.PayrollSession.fetchWithAuth(path, options);
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.detail || 'Error');
  return data;
}

form.addEventListener('submit', async (event) => {
  event.preventDefault();
  try {
    await window.PayrollSession.refreshAccessToken();
    const payload = {
      current_password: document.getElementById('current_password').value,
      new_password: document.getElementById('new_password').value,
      new_password_confirm: document.getElementById('new_password_confirm').value,
    };
    const data = await api('/api/auth/change-password', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
    message.style.color = '#12b76a';
    message.textContent = data.message;
    window.PayrollSession.clearSession();
  } catch (e) {
    message.style.color = '#b42318';
    message.textContent = e.message;
  }
});
