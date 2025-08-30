import { getCookie } from './cookies';

const BASE_URL = '/api';

let isRefreshing = false;
let failedQueue = [];

const processQueue = (error, token = null) => {
  failedQueue.forEach(prom => {
    if (error) {
      prom.reject(error);
    } else {
      prom.resolve(token);
    }
  });
  failedQueue = [];
};

const authFetch = async (url, options = {}) => {
  let accessToken = localStorage.getItem('access_token');

  const headers = {
    ...options.headers,
  };

  // FormDataの場合、ブラウザが自動でContent-Typeとboundaryを設定するので、
  // こちらで 'Content-Type': 'application/json' を設定しないようにする。
  if (!(options.body instanceof FormData)) {
    headers['Content-Type'] = 'application/json';
  }

  if (accessToken) {
    headers['Authorization'] = `Bearer ${accessToken}`;
  }

  // CSRFが必要なリクエスト（セッション認証との併用など）のために残す
  const csrfToken = getCookie('csrftoken');
  if (csrfToken && ['POST', 'PUT', 'PATCH', 'DELETE'].includes(options.method?.toUpperCase())) {
      headers['X-CSRFToken'] = csrfToken;
  }

  let response = await fetch(url, { ...options, headers });

  if (response.status === 401 && accessToken) {
    if (isRefreshing) {
      try {
        const token = await new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject });
        });
        headers['Authorization'] = `Bearer ${token}`;
        response = await fetch(url, { ...options, headers });
      } catch (err) {
        return Promise.reject(new Error('Failed to refresh token.'));
      }
    } else {
      isRefreshing = true;
      const refreshToken = localStorage.getItem('refresh_token');
      if (!refreshToken) {
        isRefreshing = false;
        window.dispatchEvent(new Event('logout'));
        return Promise.reject(new Error('No refresh token available.'));
      }

      try {
        const refreshResponse = await fetch(`${BASE_URL}/users/token/refresh/`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ refresh: refreshToken }),
        });

        if (!refreshResponse.ok) { throw new Error('Session expired'); }

        const newTokens = await refreshResponse.json();
        localStorage.setItem('access_token', newTokens.access);
        isRefreshing = false;
        processQueue(null, newTokens.access);

        headers['Authorization'] = `Bearer ${newTokens.access}`;
        response = await fetch(url, { ...options, headers });
      } catch (error) {
        isRefreshing = false;
        processQueue(error, null);
        window.dispatchEvent(new Event('logout'));
        return Promise.reject(error);
      }
    }
  }

  return response;
};

export default authFetch;