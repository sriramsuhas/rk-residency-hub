import axios from 'axios';

const BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

export const api = axios.create({
  baseURL: BASE_URL,
  paramsSerializer: {
    serialize: (params) => {
      const search = new URLSearchParams();
      Object.entries(params).forEach(([key, value]) => {
        if (value === undefined || value === null || value === '') return;
        if (Array.isArray(value)) {
          value.forEach((v) => search.append(key, v));
        } else {
          search.append(key, value);
        }
      });
      return search.toString();
    },
  },
});

function getTokens() {
  return {
    accessToken: localStorage.getItem('rk_access_token'),
    refreshToken: localStorage.getItem('rk_refresh_token'),
  };
}

export function setTokens({ accessToken, refreshToken }) {
  if (accessToken) localStorage.setItem('rk_access_token', accessToken);
  if (refreshToken) localStorage.setItem('rk_refresh_token', refreshToken);
}

export function clearTokens() {
  localStorage.removeItem('rk_access_token');
  localStorage.removeItem('rk_refresh_token');
}

api.interceptors.request.use((config) => {
  const { accessToken } = getTokens();
  if (accessToken) {
    config.headers.Authorization = `Bearer ${accessToken}`;
  }
  return config;
});

// On a 401 (expired access token), try exactly once to refresh and replay the request.
// This keeps a session alive across the 30-minute access-token lifetime without
// forcing the person to log in again every half hour.
let refreshInFlight = null;

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;
    const isAuthRoute = originalRequest?.url?.includes('/auth/');

    if (error.response?.status === 401 && !originalRequest._retry && !isAuthRoute) {
      originalRequest._retry = true;
      const { refreshToken } = getTokens();
      if (!refreshToken) {
        clearTokens();
        return Promise.reject(error);
      }

      try {
        refreshInFlight =
          refreshInFlight ||
          axios.post(`${BASE_URL}/api/v1/auth/refresh`, { refresh_token: refreshToken });
        const { data } = await refreshInFlight;
        refreshInFlight = null;
        setTokens({ accessToken: data.data.access_token });
        originalRequest.headers.Authorization = `Bearer ${data.data.access_token}`;
        return api(originalRequest);
      } catch (refreshError) {
        refreshInFlight = null;
        clearTokens();
        window.location.href = '/login';
        return Promise.reject(refreshError);
      }
    }

    return Promise.reject(error);
  }
);
