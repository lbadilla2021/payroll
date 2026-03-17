window.PayrollSession = (() => {
  let accessToken = null;
  const setToken = (token) => {
    accessToken = token;
  };
  const getHeaders = () => ({
    'Content-Type': 'application/json',
    ...(accessToken ? { Authorization: `Bearer ${accessToken}` } : {}),
  });
  async function refresh() {
    const res = await fetch('/api/auth/refresh', { method: 'POST', credentials: 'include' });
    if (!res.ok) throw new Error('No active session');
    const data = await res.json();
    setToken(data.access_token);
    return data;
  }
  return { setToken, getHeaders, refresh };
})();
