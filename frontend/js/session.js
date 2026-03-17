window.PayrollSession = (() => {
  let accessToken = null;

  function setAccessToken(token) {
    accessToken = token || null;
  }

  function getAccessToken() {
    return accessToken;
  }

  function clearSession() {
    accessToken = null;
  }

  function withAuthHeaders(headers = {}, token = accessToken) {
    const normalized = new Headers(headers);
    if (token) {
      normalized.set('Authorization', `Bearer ${token}`);
    }
    return normalized;
  }

  async function refreshAccessToken() {
    const refreshResponse = await fetch('/api/auth/refresh', {
      method: 'POST',
      credentials: 'include',
    });

    if (!refreshResponse.ok) {
      clearSession();
      throw new Error('Sesión expirada');
    }

    const data = await refreshResponse.json().catch(() => ({}));
    if (!data.access_token) {
      clearSession();
      throw new Error('Sesión inválida');
    }

    setAccessToken(data.access_token);
    return data.access_token;
  }

  async function bootstrapSession() {
    const token = await refreshAccessToken();

    const meResponse = await fetch('/api/auth/me', {
      method: 'GET',
      credentials: 'include',
      headers: withAuthHeaders({}, token),
    });

    if (!meResponse.ok) {
      clearSession();
      throw new Error('No autenticado');
    }

    return meResponse.json();
  }

  async function fetchWithAuth(url, options = {}) {
    const token = getAccessToken();

    let response = await fetch(url, {
      ...options,
      headers: withAuthHeaders(options.headers || {}, token),
      credentials: 'include',
    });

    if (response.status === 401) {
      const freshToken = await refreshAccessToken();

      response = await fetch(url, {
        ...options,
        headers: withAuthHeaders(options.headers || {}, freshToken),
        credentials: 'include',
      });

      if (response.status === 401) {
        clearSession();
        throw new Error('Sesión expirada');
      }
    }

    return response;
  }

  return {
    setAccessToken,
    getAccessToken,
    clearSession,
    refreshAccessToken,
    bootstrapSession,
    fetchWithAuth,
  };
})();
