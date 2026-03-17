window.PayrollSession = (() => {
  let accessToken = null;

  const setAccessToken = (token) => {
    accessToken = token || null;
  };

  const getAccessToken = () => accessToken;

  const clearSession = () => {
    accessToken = null;
  };

  const buildHeaders = (headers = {}) => {
    const normalized = new Headers(headers);

    if (!normalized.has('Content-Type')) {
      normalized.set('Content-Type', 'application/json');
    }

    if (accessToken) {
      normalized.set('Authorization', `Bearer ${accessToken}`);
    } else {
      normalized.delete('Authorization');
    }

    return normalized;
  };

  async function refreshAccessToken() {
    const response = await fetch('/api/auth/refresh', {
      method: 'POST',
      credentials: 'include',
    });

    if (!response.ok) {
      clearSession();
      throw new Error('No se pudo refrescar la sesión');
    }

    const data = await response.json();
    setAccessToken(data.access_token);
    return data;
  }

  async function bootstrapSession() {
    try {
      const meResponse = await fetch('/api/auth/me', {
        method: 'GET',
        credentials: 'include',
      });

      if (meResponse.ok) {
        return meResponse.json();
      }
    } catch {
      // fallback to refresh
    }

    const refreshData = await refreshAccessToken();
    if (!refreshData.access_token) {
      throw new Error('No se recibió access token');
    }

    const meResponse = await fetch('/api/auth/me', {
      method: 'GET',
      credentials: 'include',
      headers: buildHeaders(),
    });

    if (!meResponse.ok) {
      throw new Error('No se pudo recuperar el usuario');
    }

    return meResponse.json();
  }

  async function fetchWithAuth(path, options = {}) {
    const requestOptions = {
      ...options,
      credentials: 'include',
      headers: buildHeaders(options.headers || {}),
    };

    let response = await fetch(path, requestOptions);

    if (response.status === 401) {
      try {
        await refreshAccessToken();
      } catch {
        clearSession();
        throw new Error('Sesión expirada');
      }

      response = await fetch(path, {
        ...options,
        credentials: 'include',
        headers: buildHeaders(options.headers || {}),
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
