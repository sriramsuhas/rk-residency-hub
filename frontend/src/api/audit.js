import { api } from './client';

export const auditApi = {
  search: (params) => api.get('/api/v1/audit-logs', { params }),
};
