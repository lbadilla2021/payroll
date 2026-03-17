window.PayrollSession = (() => {
  let accessToken = null;

  const setToken = (token) => {
    accessToken = token || null;
  };

  const clear = () => {
    accessToken = null;
  };

  const authHeaders = (extra = {}) => ({
    'Content-Type': 'application/json',
    ...(accessToken ? { Authorization: `Bearer ${accessToken}` } : {}),
    ...extra,
  });

  async function refresh() {
    const res = await fetch('/api/auth/refresh', { method: 'POST', credentials: 'include' });
    if (!res.ok) {
      clear();
      throw new Error('Sesión expirada');
    }
    const data = await res.json();
    setToken(data.access_token);
    return data;
  }

  async function fetchWithAuth(path, options = {}) {
    if (!accessToken) {
      await refresh();
    }

    let res = await fetch(path, {
      ...options,
      credentials: 'include',
      headers: authHeaders(options.headers || {}),
    });

    if (res.status === 401) {
      await refresh();
      res = await fetch(path, {
        ...options,
        credentials: 'include',
        headers: authHeaders(options.headers || {}),
      });
    }

    return res;
  }

  return { setToken, clear, refresh, fetchWithAuth };
})();
