import { api } from './client';

export const analyticsApi = {
  owner: () => api.get('/api/v1/analytics/owner'),
  reception: () => api.get('/api/v1/analytics/reception'),
  housekeeping: () => api.get('/api/v1/analytics/housekeeping'),
};
