import { api } from './client';

export const reviewsApi = {
  create: (bookingId, rating, comment) => api.post('/api/v1/reviews', { booking_id: bookingId, rating, comment }),
  update: (id, payload) => api.put(`/api/v1/reviews/${id}`, payload),
  delete: (id) => api.delete(`/api/v1/reviews/${id}`),
  myReviews: (params) => api.get('/api/v1/reviews/me', { params }),
  forRoom: (roomId, params) => api.get(`/api/v1/rooms/${roomId}/reviews`, { params }),
};
