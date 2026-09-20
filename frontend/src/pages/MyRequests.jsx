import { useCallback, useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import TopNav from '../components/TopNav';
import { maintenanceApi } from '../api/maintenance';
import '../styles/status.css';
import './MyRequests.css';

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

const STATUS_LABEL = {
  PENDING: 'Pending',
  ASSIGNED: 'Assigned',
  IN_PROGRESS: 'In progress',
  COMPLETED: 'Completed',
  CANCELLED: 'Cancelled',
};

export default function MyRequests() {
  const [requests, setRequests] = useState([]);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState('');
  const [cancellingId, setCancellingId] = useState(null);
  const [error, setError] = useState('');

  const load = useCallback(() => {
    setLoading(true);
    maintenanceApi
      .myRequests({ status: statusFilter || undefined, page_size: 50 })
      .then((res) => setRequests(res.data.data.items))
      .catch(() => setError('Could not load your requests.'))
      .finally(() => setLoading(false));
  }, [statusFilter]);

  useEffect(() => {
    load();
  }, [load]);

  async function handleCancel(id) {
    setCancellingId(id);
    try {
      await maintenanceApi.cancel(id, 'Cancelled by guest');
      load();
    } catch (err) {
      setError(err.response?.data?.message || 'Could not cancel this request.');
    } finally {
      setCancellingId(null);
    }
  }

  return (
    <div>
      <TopNav />
      <div className="myrequests-page">
        <div className="myrequests-header">
          <h1>My maintenance requests</h1>
          <div className="myrequests-header__actions">
            <select value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)}>
              <option value="">All statuses</option>
              <option value="PENDING">Pending</option>
              <option value="ASSIGNED">Assigned</option>
              <option value="IN_PROGRESS">In progress</option>
              <option value="COMPLETED">Completed</option>
              <option value="CANCELLED">Cancelled</option>
            </select>
            <Link to="/raise-request" className="btn-primary myrequests-new-btn">
              New request
            </Link>
          </div>
        </div>

        {error && <div className="alert alert-error">{error}</div>}
        {loading && <p className="listing-status">Loading…</p>}
        {!loading && requests.length === 0 && <p className="listing-status">No maintenance requests yet.</p>}

        <div className="request-list">
          {requests.map((r) => (
            <div className="request-row" key={r.id}>
              {r.image_url ? (
                <img className="request-row__image" src={`${API_BASE}${r.image_url}`} alt="" />
              ) : (
                <div className="request-row__image request-row__image--placeholder">{r.category[0]}</div>
              )}
              <div className="request-row__body">
                <div className="request-row__top">
                  <h3>
                    {r.category.charAt(0) + r.category.slice(1).toLowerCase()} · Room {r.room.room_number}
                  </h3>
                  <span className={`booking-status booking-status--${r.status.toLowerCase()}`}>
                    {STATUS_LABEL[r.status]}
                  </span>
                </div>
                <p className="request-row__desc">{r.description}</p>
                {r.assigned_staff && (
                  <p className="request-row__meta">Assigned to {r.assigned_staff.full_name}</p>
                )}
                {r.status === 'COMPLETED' && r.remarks && (
                  <p className="request-row__meta">Resolution: {r.remarks}</p>
                )}
              </div>
              {(r.status === 'PENDING' || r.status === 'ASSIGNED') && (
                <button
                  className="request-row__cancel-btn"
                  onClick={() => handleCancel(r.id)}
                  disabled={cancellingId === r.id}
                >
                  {cancellingId === r.id ? 'Cancelling…' : 'Cancel'}
                </button>
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
