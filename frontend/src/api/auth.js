import { api } from './client';

export const authApi = {
  register: (payload) => api.post('/api/v1/auth/register', payload),
  login: (payload) => api.post('/api/v1/auth/login', payload),
  logout: (refreshToken) => api.post('/api/v1/auth/logout', { refresh_token: refreshToken }),
  forgotPassword: (email) => api.post('/api/v1/auth/forgot-password', { email }),
  resetPassword: (token, newPassword) =>
    api.post('/api/v1/auth/reset-password', { token, new_password: newPassword }),
  changePassword: (currentPassword, newPassword) =>
    api.post('/api/v1/auth/change-password', {
      current_password: currentPassword,
      new_password: newPassword,
    }),
};

export const userApi = {
  me: () => api.get('/api/v1/users/me'),
  updateProfile: (payload) => api.put('/api/v1/users/me', payload),
};
