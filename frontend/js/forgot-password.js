const form = document.getElementById('forgot-form');
const message = document.getElementById('message');
form.addEventListener('submit', async (event) => {
  event.preventDefault();
  const payload = {
    tenant_code: document.getElementById('tenant_code').value || null,
    email: document.getElementById('email').value,
  };
  await fetch('/api/auth/forgot-password', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  message.style.color = '#12b76a';
  message.textContent = 'Si la cuenta existe, recibirás instrucciones por correo.';
});
