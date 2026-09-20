import { api } from './client';

export const paymentsApi = {
  pay: (bookingId, method) => api.post(`/api/v1/bookings/${bookingId}/pay`, { method }),
  myPayments: (params) => api.get('/api/v1/payments/me', { params }),
  getInvoice: (bookingId) => api.get(`/api/v1/bookings/${bookingId}/invoice`),
  refund: (paymentId, reason) => api.post(`/api/v1/payments/${paymentId}/refund`, { reason }),

  // The PDF route requires auth, so a plain <a href> can't carry the bearer
  // token — fetch it as a blob through the authenticated client instead and
  // trigger the browser's download via a temporary object URL.
  async downloadInvoicePdf(bookingId, invoiceNumber) {
    const res = await api.get(`/api/v1/bookings/${bookingId}/invoice/pdf`, { responseType: 'blob' });
    const url = window.URL.createObjectURL(new Blob([res.data], { type: 'application/pdf' }));
    const link = document.createElement('a');
    link.href = url;
    link.download = `${invoiceNumber || 'invoice'}.pdf`;
    document.body.appendChild(link);
    link.click();
    link.remove();
    window.URL.revokeObjectURL(url);
  },
};
