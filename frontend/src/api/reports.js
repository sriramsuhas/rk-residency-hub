import { api } from './client';

export const reportsApi = {
  async download(reportType, params, filenameHint) {
    const res = await api.get(`/api/v1/reports/${reportType}`, { params, responseType: 'blob' });
    const contentType = res.headers['content-type'] || 'application/octet-stream';
    const disposition = res.headers['content-disposition'] || '';
    const match = disposition.match(/filename="?([^"]+)"?/);
    const filename = match ? match[1] : filenameHint || `${reportType}-report`;

    const url = window.URL.createObjectURL(new Blob([res.data], { type: contentType }));
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    link.remove();
    window.URL.revokeObjectURL(url);
  },
};
