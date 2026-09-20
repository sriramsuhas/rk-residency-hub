import { api } from './client';

export const maintenanceApi = {
  create: (formData) =>
    api.post('/api/v1/maintenance-requests', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    }),
  myRequests: (params) => api.get('/api/v1/maintenance-requests/me', { params }),
  myTasks: (params) => api.get('/api/v1/maintenance-requests/my-tasks', { params }),
  getById: (id) => api.get(`/api/v1/maintenance-requests/${id}`),
  searchAll: (params) => api.get('/api/v1/maintenance-requests', { params }),
  assign: (id, staffId, priority) =>
    api.patch(`/api/v1/maintenance-requests/${id}/assign`, { staff_id: staffId, priority }),
  start: (id) => api.post(`/api/v1/maintenance-requests/${id}/start`),
  complete: (id, formData) =>
    api.post(`/api/v1/maintenance-requests/${id}/complete`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    }),
  cancel: (id, reason) => api.post(`/api/v1/maintenance-requests/${id}/cancel`, { reason }),
  stats: () => api.get('/api/v1/maintenance-requests/stats'),
};
