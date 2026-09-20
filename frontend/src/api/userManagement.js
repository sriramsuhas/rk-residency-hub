import { api } from './client';

export const userManagementApi = {
  list: (params) => api.get('/api/v1/users', { params }),
  changeRole: (userId, role) => api.patch(`/api/v1/users/${userId}/role`, { role }),
  changeStatus: (userId, isActive) => api.patch(`/api/v1/users/${userId}/status`, { is_active: isActive }),
};
