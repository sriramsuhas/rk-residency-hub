import { api } from './client';

export const roomsApi = {
  search: (params) => api.get('/api/v1/rooms', { params }),
  getById: (id) => api.get(`/api/v1/rooms/${id}`),
  floors: () => api.get('/api/v1/floors'),
  roomTypes: () => api.get('/api/v1/room-types'),
  amenities: () => api.get('/api/v1/amenities'),

  // Owner-only management
  create: (payload) => api.post('/api/v1/rooms', payload),
  update: (id, payload) => api.put(`/api/v1/rooms/${id}`, payload),
  deactivate: (id) => api.delete(`/api/v1/rooms/${id}`),
  setAmenities: (id, amenityIds) => api.patch(`/api/v1/rooms/${id}/amenities`, { amenity_ids: amenityIds }),
  uploadImage: (id, file, isPrimary) => {
    const form = new FormData();
    form.append('file', file);
    return api.post(`/api/v1/rooms/${id}/images`, form, {
      params: { is_primary: isPrimary },
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },
  deleteImage: (roomId, imageId) => api.delete(`/api/v1/rooms/${roomId}/images/${imageId}`),

  createFloor: (payload) => api.post('/api/v1/floors', payload),
  createRoomType: (payload) => api.post('/api/v1/room-types', payload),
  createAmenity: (payload) => api.post('/api/v1/amenities', payload),
};

