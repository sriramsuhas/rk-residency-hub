import { api } from './client';

export const bookingsApi = {
  checkAvailability: (roomId, checkIn, checkOut) =>
    api.get(`/api/v1/rooms/${roomId}/availability`, { params: { check_in: checkIn, check_out: checkOut } }),
  create: (payload) => api.post('/api/v1/bookings', payload),
  myBookings: (params) => api.get('/api/v1/bookings/me', { params }),
  getById: (id) => api.get(`/api/v1/bookings/${id}`),
  cancel: (id, reason) => api.post(`/api/v1/bookings/${id}/cancel`, { reason }),
  searchAll: (params) => api.get('/api/v1/bookings', { params }),
  checkIn: (id) => api.post(`/api/v1/bookings/${id}/check-in`),
  checkOut: (id) => api.post(`/api/v1/bookings/${id}/check-out`),
};
