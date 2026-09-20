import { api } from './client';

export const notificationsApi = {
  list: (params) => api.get('/api/v1/notifications', { params }),
  markRead: (id) => api.patch(`/api/v1/notifications/${id}/read`),
  markAllRead: () => api.patch('/api/v1/notifications/read-all'),
};
