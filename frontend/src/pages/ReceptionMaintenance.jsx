import { useCallback, useEffect, useState } from 'react';
import TopNav from '../components/TopNav';
import { maintenanceApi } from '../api/maintenance';
import { api } from '../api/client';
import '../styles/status.css';
import './ReceptionMaintenance.css';

export default function ReceptionMaintenance() {
  const [requests, setRequests] = useState([]);
  const [staffOptions, setStaffOptions] = useState([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState('');
  const [error, setError] = useState('');
  const [assigningId, setAssigningId] = useState(null);
  const [selectedStaff, setSelectedStaff] = useState('');

  const load = useCallback(() => {
    setLoading(true);
    setError('');
    maintenanceApi
      .searchAll({ status: statusFilter || undefined, page_size: 50 })
      .then((res) => {
        setRequests(res.data.data.items);
        setTotal(res.data.data.total);
      })
      .catch(() => setError('Could not load maintenance requests.'))
      .finally(() => setLoading(false));
  }, [statusFilter]);

  useEffect(() => {
    load();
  }, [load]);

  useEffect(() => {
    api.get('/api/v1/users', { params: { role: 'HOUSEKEEPING', page_size: 50 } }).then((res) => {
      setStaffOptions(res.data.data.items);
    });
  }, []);

  function openAssignForm(id) {
    setAssigningId(id);
    setSelectedStaff('');
  }

  async function handleAssign(id) {
    if (!selectedStaff) return;
    setError('');
    try {
      await maintenanceApi.assign(id, Number(selectedStaff));
      setAssigningId(null);
      load();
    } catch (err) {
      setError(err.response?.data?.message || 'Could not assign this request.');
    }
  }

  return (
    <div>
      <TopNav />
      <div className="reception-maint-page">
        <div className="reception-maint-header">
          <div>
            <h1>Maintenance requests</h1>
            <p>{total} request{total === 1 ? '' : 's'}</p>
          </div>
          <select value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)}>
            <option value="">All statuses</option>
            <option value="PENDING">Pending</option>
            <option value="ASSIGNED">Assigned</option>
            <option value="IN_PROGRESS">In progress</option>
            <option value="COMPLETED">Completed</option>
            <option value="CANCELLED">Cancelled</option>
          </select>
        </div>

        {error && <div className="alert alert-error">{error}</div>}
        {loading && <p className="listing-status">Loading…</p>}

        <div className="reception-maint-list">
          {requests.map((r) => (
            <div className="reception-maint-row" key={r.id}>
              <div className="reception-maint-row__main">
                <div className="reception-maint-row__top">
                  <h3>
                    {r.category.charAt(0) + r.category.slice(1).toLowerCase()} · Room {r.room.room_number}
                  </h3>
                  <span className={`booking-status booking-status--${r.status.toLowerCase()}`}>
                    {r.status.replace('_', ' ')}
                  </span>
                </div>
                <p className="reception-maint-row__meta">
                  {r.customer.full_name} · Priority: {r.priority}
                  {r.assigned_staff && ` · Assigned to ${r.assigned_staff.full_name}`}
                </p>
                <p className="reception-maint-row__desc">{r.description}</p>
              </div>

              {(r.status === 'PENDING' || r.status === 'ASSIGNED') && (
                <div className="reception-maint-row__actions">
                  {assigningId === r.id ? (
                    <div className="reception-maint-row__assign-form">
                      <select value={selectedStaff} onChange={(e) => setSelectedStaff(e.target.value)}>
                        <option value="">Choose staff</option>
                        {staffOptions.map((s) => (
                          <option key={s.id} value={s.id}>
                            {s.full_name}
                          </option>
                        ))}
                      </select>
                      <button onClick={() => handleAssign(r.id)} disabled={!selectedStaff}>
                        Confirm
                      </button>
                    </div>
                  ) : (
                    <button onClick={() => openAssignForm(r.id)}>
                      {r.status === 'PENDING' ? 'Assign' : 'Reassign'}
                    </button>
                  )}
                </div>
              )}
            </div>
          ))}
        </div>

        {!loading && requests.length === 0 && <p className="listing-status">No maintenance requests found.</p>}
      </div>
    </div>
  );
}
