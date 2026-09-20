import { useCallback, useEffect, useState } from 'react';
import TopNav from '../components/TopNav';
import { maintenanceApi } from '../api/maintenance';
import '../styles/status.css';
import '../styles/forms.css';
import HousekeepingDashboardStats from './HousekeepingDashboardStats';
import './MyTasks.css';

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

export default function MyTasks() {
  const [tasks, setTasks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState('');
  const [error, setError] = useState('');
  const [actingId, setActingId] = useState(null);
  const [completingId, setCompletingId] = useState(null);
  const [remarks, setRemarks] = useState('');
  const [completionImage, setCompletionImage] = useState(null);

  const load = useCallback(() => {
    setLoading(true);
    maintenanceApi
      .myTasks({ status: statusFilter || undefined, page_size: 50 })
      .then((res) => setTasks(res.data.data.items))
      .catch(() => setError('Could not load your tasks.'))
      .finally(() => setLoading(false));
  }, [statusFilter]);

  useEffect(() => {
    load();
  }, [load]);

  async function handleStart(id) {
    setActingId(id);
    setError('');
    try {
      await maintenanceApi.start(id);
      load();
    } catch (err) {
      setError(err.response?.data?.message || 'Could not start this task.');
    } finally {
      setActingId(null);
    }
  }

  function openCompleteForm(id) {
    setCompletingId(id);
    setRemarks('');
    setCompletionImage(null);
  }

  async function handleComplete(id) {
    setActingId(id);
    setError('');
    try {
      const formData = new FormData();
      if (remarks) formData.append('remarks', remarks);
      if (completionImage) formData.append('image', completionImage);
      await maintenanceApi.complete(id, formData);
      setCompletingId(null);
      load();
    } catch (err) {
      setError(err.response?.data?.message || 'Could not complete this task.');
    } finally {
      setActingId(null);
    }
  }

  return (
    <div>
      <TopNav />
      <div className="mytasks-page">
        <HousekeepingDashboardStats />
        <div className="mytasks-header">
          <h1>My tasks</h1>
          <select value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)}>
            <option value="">All statuses</option>
            <option value="ASSIGNED">Assigned</option>
            <option value="IN_PROGRESS">In progress</option>
            <option value="COMPLETED">Completed</option>
          </select>
        </div>

        {error && <div className="alert alert-error">{error}</div>}
        {loading && <p className="listing-status">Loading…</p>}
        {!loading && tasks.length === 0 && <p className="listing-status">No tasks assigned to you right now.</p>}

        <div className="task-list">
          {tasks.map((t) => (
            <div className="task-card" key={t.id}>
              <div className="task-card__top">
                <div>
                  <h3>
                    {t.category.charAt(0) + t.category.slice(1).toLowerCase()} · Room {t.room.room_number}
                  </h3>
                  <p className="task-card__priority">Priority: {t.priority}</p>
                </div>
                <span className={`booking-status booking-status--${t.status.toLowerCase()}`}>
                  {t.status.replace('_', ' ')}
                </span>
              </div>

              <p className="task-card__desc">{t.description}</p>
              {t.image_url && (
                <img className="task-card__image" src={`${API_BASE}${t.image_url}`} alt="Reported issue" />
              )}

              {t.status === 'ASSIGNED' && (
                <button className="btn-primary" onClick={() => handleStart(t.id)} disabled={actingId === t.id}>
                  {actingId === t.id ? 'Starting…' : 'Accept task'}
                </button>
              )}

              {t.status === 'IN_PROGRESS' && completingId !== t.id && (
                <button className="btn-primary" onClick={() => openCompleteForm(t.id)}>
                  Mark completed
                </button>
              )}

              {t.status === 'IN_PROGRESS' && completingId === t.id && (
                <div className="task-card__complete-form">
                  <div className="form-field">
                    <label>Remarks</label>
                    <textarea
                      rows={2}
                      value={remarks}
                      onChange={(e) => setRemarks(e.target.value)}
                      placeholder="What did you fix?"
                    />
                  </div>
                  <div className="form-field">
                    <label>Completion photo (optional)</label>
                    <input
                      type="file"
                      accept="image/png, image/jpeg, image/webp"
                      onChange={(e) => setCompletionImage(e.target.files?.[0] || null)}
                    />
                  </div>
                  <div className="task-card__complete-actions">
                    <button className="btn-primary" onClick={() => handleComplete(t.id)} disabled={actingId === t.id}>
                      {actingId === t.id ? 'Saving…' : 'Confirm completion'}
                    </button>
                    <button className="btn-link" onClick={() => setCompletingId(null)}>
                      Cancel
                    </button>
                  </div>
                </div>
              )}

              {t.status === 'COMPLETED' && t.remarks && (
                <p className="task-card__resolution">Resolution: {t.remarks}</p>
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
