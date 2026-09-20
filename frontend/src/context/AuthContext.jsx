import { createContext, useContext, useEffect, useState } from 'react';
import { authApi, userApi } from '../api/auth';
import { clearTokens, setTokens } from '../api/client';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const hasToken = Boolean(localStorage.getItem('rk_access_token'));
    if (!hasToken) {
      setLoading(false);
      return;
    }
    userApi
      .me()
      .then((res) => setUser(res.data.data))
      .catch(() => clearTokens())
      .finally(() => setLoading(false));
  }, []);

  async function login(email, password) {
    const res = await authApi.login({ email, password });
    const { access_token, refresh_token } = res.data.data;
    setTokens({ accessToken: access_token, refreshToken: refresh_token });
    const me = await userApi.me();
    setUser(me.data.data);
    return me.data.data;
  }

  async function register(payload) {
    await authApi.register(payload);
    return login(payload.email, payload.password);
  }

  async function logout() {
    const refreshToken = localStorage.getItem('rk_refresh_token');
    try {
      if (refreshToken) await authApi.logout(refreshToken);
    } finally {
      clearTokens();
      setUser(null);
    }
  }

  function refreshCurrentUser() {
    return userApi.me().then((res) => {
      setUser(res.data.data);
      return res.data.data;
    });
  }

  return (
    <AuthContext.Provider value={{ user, loading, login, register, logout, refreshCurrentUser }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within AuthProvider');
  return ctx;
}
