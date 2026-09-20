import { useState } from 'react';
import TopNav from '../components/TopNav';
import { useAuth } from '../context/AuthContext';
import { reportsApi } from '../api/reports';
import '../styles/forms.css';
import './Reports.css';

function todayIso() {
  return new Date().toISOString().slice(0, 10);
}

function daysAgoIso(days) {
  const d = new Date();
  d.setDate(d.getDate() - days);
  return d.toISOString().slice(0, 10);
}

const REPORT_TYPES = [
  { key: 'revenue', label: 'Revenue Report', description: 'Every successful payment in the date range, with a total.' },
  { key: 'bookings', label: 'Booking Report', description: 'All bookings created in the date range, with their current status.' },
  { key: 'maintenance', label: 'Maintenance Report', description: 'All maintenance requests raised in the date range.' },
  { key: 'occupancy', label: 'Occupancy Report', description: 'Day-by-day occupancy rate across the date range.' },
];

export default function Reports() {
  const { user } = useAuth();
  const [dateFrom, setDateFrom] = useState(daysAgoIso(30));
  const [dateTo, setDateTo] = useState(todayIso());
  const [downloadingKey, setDownloadingKey] = useState(null);
  const [error, setError] = useState('');

  async function handleDownload(reportType, format) {
    setDownloadingKey(`${reportType}-${format}`);
    setError('');
    try {
      const params = { format };
      if (reportType !== 'customers') {
        params.date_from = dateFrom;
        params.date_to = dateTo;
      }
      await reportsApi.download(reportType, params);
    } catch (err) {
      setError('Could not generate that report. Please try again.');
    } finally {
      setDownloadingKey(null);
    }
  }

  return (
    <div>
      <TopNav />
      <div className="reports-page">
        <h1>Reports</h1>
        <p className="reports-subtitle">Export operational data as CSV or PDF.</p>

        {error && <div className="alert alert-error">{error}</div>}

        <div className="reports-range">
          <div className="form-field">
            <label>From</label>
            <input type="date" value={dateFrom} onChange={(e) => setDateFrom(e.target.value)} max={dateTo} />
          </div>
          <div className="form-field">
            <label>To</label>
            <input type="date" value={dateTo} onChange={(e) => setDateTo(e.target.value)} min={dateFrom} max={todayIso()} />
          </div>
        </div>

        <div className="reports-list">
          {REPORT_TYPES.map((rt) => (
            <div className="report-card" key={rt.key}>
              <div>
                <h3>{rt.label}</h3>
                <p>{rt.description}</p>
              </div>
              <div className="report-card__actions">
                <button
                  onClick={() => handleDownload(rt.key, 'csv')}
                  disabled={downloadingKey === `${rt.key}-csv`}
                >
                  {downloadingKey === `${rt.key}-csv` ? 'Downloading…' : 'CSV'}
                </button>
                <button
                  onClick={() => handleDownload(rt.key, 'pdf')}
                  disabled={downloadingKey === `${rt.key}-pdf`}
                >
                  {downloadingKey === `${rt.key}-pdf` ? 'Downloading…' : 'PDF'}
                </button>
              </div>
            </div>
          ))}

          {user?.role === 'OWNER' && (
            <div className="report-card">
              <div>
                <h3>Customer Report</h3>
                <p>All customers with their booking count and total spend to date.</p>
              </div>
              <div className="report-card__actions">
                <button
                  onClick={() => handleDownload('customers', 'csv')}
                  disabled={downloadingKey === 'customers-csv'}
                >
                  {downloadingKey === 'customers-csv' ? 'Downloading…' : 'CSV'}
                </button>
                <button
                  onClick={() => handleDownload('customers', 'pdf')}
                  disabled={downloadingKey === 'customers-pdf'}
                >
                  {downloadingKey === 'customers-pdf' ? 'Downloading…' : 'PDF'}
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
