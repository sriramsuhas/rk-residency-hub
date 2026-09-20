import { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import TopNav from '../components/TopNav';
import { roomsApi } from '../api/rooms';
import { maintenanceApi } from '../api/maintenance';
import '../styles/forms.css';
import './RaiseMaintenanceRequest.css';

const CATEGORIES = ['AC', 'WATER', 'ELECTRICITY', 'WIFI', 'BATHROOM', 'FURNITURE', 'CLEANING', 'OTHER'];
const PRIORITIES = ['LOW', 'MEDIUM', 'HIGH', 'URGENT'];

export default function RaiseMaintenanceRequest() {
  const navigate = useNavigate();
  const [rooms, setRooms] = useState([]);
  const [roomId, setRoomId] = useState('');
  const [category, setCategory] = useState('AC');
  const [priority, setPriority] = useState('MEDIUM');
  const [description, setDescription] = useState('');
  const [image, setImage] = useState(null);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    roomsApi.search({ page_size: 50 }).then((res) => setRooms(res.data.data.items));
  }, []);

  async function handleSubmit(e) {
    e.preventDefault();
    setError('');

    if (!roomId) {
      setError('Please select which room this is about.');
      return;
    }
    if (description.trim().length < 5) {
      setError('Please describe the issue in a bit more detail.');
      return;
    }

    setSubmitting(true);
    try {
      const formData = new FormData();
      formData.append('room_id', roomId);
      formData.append('category', category);
      formData.append('priority', priority);
      formData.append('description', description);
      if (image) formData.append('image', image);

      await maintenanceApi.create(formData);
      setSuccess(true);
      setTimeout(() => navigate('/my-requests'), 1200);
    } catch (err) {
      setError(err.response?.data?.message || 'Could not submit your request. Please try again.');
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div>
      <TopNav />
      <div className="raise-request-page">
        <h1>Raise a maintenance request</h1>
        <p className="raise-request-subtitle">Tell us what's wrong and we'll get someone on it.</p>

        {success && <div className="alert alert-success">Request submitted! Redirecting to your requests…</div>}
        {error && <div className="alert alert-error">{error}</div>}

        {!success && (
          <form onSubmit={handleSubmit} noValidate>
            <div className="form-field">
              <label htmlFor="room">Which room?</label>
              <select id="room" value={roomId} onChange={(e) => setRoomId(e.target.value)} required>
                <option value="">Select a room</option>
                {rooms.map((r) => (
                  <option key={r.id} value={r.id}>
                    Room {r.room_number} · {r.room_type.name}
                  </option>
                ))}
              </select>
            </div>

            <div className="raise-request-row">
              <div className="form-field">
                <label htmlFor="category">Category</label>
                <select id="category" value={category} onChange={(e) => setCategory(e.target.value)}>
                  {CATEGORIES.map((c) => (
                    <option key={c} value={c}>
                      {c.charAt(0) + c.slice(1).toLowerCase()}
                    </option>
                  ))}
                </select>
              </div>
              <div className="form-field">
                <label htmlFor="priority">Priority</label>
                <select id="priority" value={priority} onChange={(e) => setPriority(e.target.value)}>
                  {PRIORITIES.map((p) => (
                    <option key={p} value={p}>
                      {p.charAt(0) + p.slice(1).toLowerCase()}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            <div className="form-field">
              <label htmlFor="description">Describe the issue</label>
              <textarea
                id="description"
                rows={4}
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="e.g. The AC in the room isn't cooling and makes a rattling noise."
                required
              />
            </div>

            <div className="form-field">
              <label htmlFor="image">Photo (optional)</label>
              <input
                id="image"
                type="file"
                accept="image/png, image/jpeg, image/webp"
                onChange={(e) => setImage(e.target.files?.[0] || null)}
              />
            </div>

            <button className="btn-primary" type="submit" disabled={submitting}>
              {submitting ? 'Submitting…' : 'Submit request'}
            </button>
          </form>
        )}

        <p className="auth-footer-note">
          <Link to="/my-requests">View your maintenance requests</Link>
        </p>
      </div>
    </div>
  );
}
