import { useCallback, useEffect, useState } from 'react';
import TopNav from '../components/TopNav';
import { roomsApi } from '../api/rooms';
import '../styles/forms.css';
import './RoomListing.css';
import './ManageRooms.css';

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

const emptyForm = {
  room_number: '',
  floor_id: '',
  room_type_id: '',
  price_per_night: '',
  capacity: '',
  description: '',
  amenity_ids: [],
};

export default function ManageRooms() {
  const [rooms, setRooms] = useState([]);
  const [floors, setFloors] = useState([]);
  const [roomTypes, setRoomTypes] = useState([]);
  const [amenities, setAmenities] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  const [formOpen, setFormOpen] = useState(false);
  const [editingId, setEditingId] = useState(null);
  const [form, setForm] = useState(emptyForm);
  const [submitting, setSubmitting] = useState(false);

  const [newFloorName, setNewFloorName] = useState('');
  const [newFloorNumber, setNewFloorNumber] = useState('');
  const [newTypeName, setNewTypeName] = useState('');
  const [newTypePrice, setNewTypePrice] = useState('');
  const [newTypeOccupancy, setNewTypeOccupancy] = useState('');
  const [newAmenityName, setNewAmenityName] = useState('');

  const [uploadingRoomId, setUploadingRoomId] = useState(null);

  const loadLookups = useCallback(() => {
    Promise.all([roomsApi.floors(), roomsApi.roomTypes(), roomsApi.amenities()]).then(
      ([f, t, a]) => {
        setFloors(f.data.data);
        setRoomTypes(t.data.data);
        setAmenities(a.data.data);
      }
    );
  }, []);

  const loadRooms = useCallback(() => {
    setLoading(true);
    roomsApi
      .search({ page_size: 100 })
      .then((res) => setRooms(res.data.data.items))
      .catch(() => setError('Could not load rooms.'))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    loadLookups();
    loadRooms();
  }, [loadLookups, loadRooms]);

  function resetForm() {
    setForm(emptyForm);
    setEditingId(null);
  }

  function openCreateForm() {
    resetForm();
    setFormOpen(true);
    setSuccess('');
    setError('');
  }

  async function openEditForm(roomSummary) {
    setError('');
    setSuccess('');
    const res = await roomsApi.getById(roomSummary.id);
    const room = res.data.data;
    setForm({
      room_number: room.room_number,
      floor_id: room.floor.id,
      room_type_id: room.room_type.id,
      price_per_night: room.price_per_night,
      capacity: room.capacity,
      description: room.description || '',
      amenity_ids: room.amenities.map((a) => a.id),
    });
    setEditingId(room.id);
    setFormOpen(true);
  }

  function toggleAmenity(id) {
    setForm((prev) => ({
      ...prev,
      amenity_ids: prev.amenity_ids.includes(id)
        ? prev.amenity_ids.filter((a) => a !== id)
        : [...prev.amenity_ids, id],
    }));
  }

  async function handleSubmit(e) {
    e.preventDefault();
    setError('');
    setSubmitting(true);
    try {
      const payload = {
        room_number: form.room_number,
        floor_id: Number(form.floor_id),
        room_type_id: Number(form.room_type_id),
        price_per_night: Number(form.price_per_night),
        capacity: Number(form.capacity),
        description: form.description || null,
      };

      if (editingId) {
        await roomsApi.update(editingId, payload);
        await roomsApi.setAmenities(editingId, form.amenity_ids);
        setSuccess(`Room ${form.room_number} updated.`);
      } else {
        await roomsApi.create({ ...payload, amenity_ids: form.amenity_ids });
        setSuccess(`Room ${form.room_number} created.`);
      }
      setFormOpen(false);
      resetForm();
      loadRooms();
    } catch (err) {
      setError(err.response?.data?.message || 'Could not save this room.');
    } finally {
      setSubmitting(false);
    }
  }

  async function handleDeactivate(room) {
    if (!window.confirm(`Deactivate Room ${room.room_number}? It will stop appearing in search.`)) return;
    try {
      await roomsApi.deactivate(room.id);
      loadRooms();
    } catch (err) {
      setError(err.response?.data?.message || 'Could not deactivate this room.');
    }
  }

  async function handleImageUpload(roomId, file) {
    setUploadingRoomId(roomId);
    try {
      await roomsApi.uploadImage(roomId, file, true);
      loadRooms();
    } catch (err) {
      setError(err.response?.data?.message || 'Could not upload image.');
    } finally {
      setUploadingRoomId(null);
    }
  }

  async function handleQuickAddFloor() {
    if (!newFloorName || newFloorNumber === '') return;
    try {
      const res = await roomsApi.createFloor({ name: newFloorName, floor_number: Number(newFloorNumber) });
      setFloors((prev) => [...prev, res.data.data]);
      setForm((prev) => ({ ...prev, floor_id: res.data.data.id }));
      setNewFloorName('');
      setNewFloorNumber('');
    } catch (err) {
      setError(err.response?.data?.message || 'Could not add floor.');
    }
  }

  async function handleQuickAddType() {
    if (!newTypeName || !newTypePrice || !newTypeOccupancy) return;
    try {
      const res = await roomsApi.createRoomType({
        name: newTypeName,
        base_price: Number(newTypePrice),
        max_occupancy: Number(newTypeOccupancy),
      });
      setRoomTypes((prev) => [...prev, res.data.data]);
      setForm((prev) => ({ ...prev, room_type_id: res.data.data.id }));
      setNewTypeName('');
      setNewTypePrice('');
      setNewTypeOccupancy('');
    } catch (err) {
      setError(err.response?.data?.message || 'Could not add room type.');
    }
  }

  async function handleQuickAddAmenity() {
    if (!newAmenityName) return;
    try {
      const res = await roomsApi.createAmenity({ name: newAmenityName });
      setAmenities((prev) => [...prev, res.data.data]);
      setForm((prev) => ({ ...prev, amenity_ids: [...prev.amenity_ids, res.data.data.id] }));
      setNewAmenityName('');
    } catch (err) {
      setError(err.response?.data?.message || 'Could not add amenity.');
    }
  }

  return (
    <div>
      <TopNav />
      <div className="manage-rooms-page">
        <div className="manage-rooms-header">
          <div>
            <h1>Manage rooms</h1>
            <p>{rooms.length} active room{rooms.length === 1 ? '' : 's'}</p>
          </div>
          {!formOpen && (
            <button className="btn-primary manage-rooms-add-btn" onClick={openCreateForm}>
              + Add room
            </button>
          )}
        </div>

        {success && <div className="alert alert-success">{success}</div>}
        {error && <div className="alert alert-error">{error}</div>}

        {formOpen && (
          <form className="room-form" onSubmit={handleSubmit}>
            <h2>{editingId ? `Edit Room ${form.room_number}` : 'New room'}</h2>

            <div className="room-form__row">
              <div className="form-field">
                <label>Room number</label>
                <input
                  value={form.room_number}
                  onChange={(e) => setForm({ ...form, room_number: e.target.value })}
                  required
                />
              </div>
              <div className="form-field">
                <label>Price per night (Rs.)</label>
                <input
                  type="number"
                  min="1"
                  value={form.price_per_night}
                  onChange={(e) => setForm({ ...form, price_per_night: e.target.value })}
                  required
                />
              </div>
              <div className="form-field">
                <label>Capacity (guests)</label>
                <input
                  type="number"
                  min="1"
                  value={form.capacity}
                  onChange={(e) => setForm({ ...form, capacity: e.target.value })}
                  required
                />
              </div>
            </div>

            <div className="room-form__row">
              <div className="form-field">
                <label>Floor</label>
                <select
                  value={form.floor_id}
                  onChange={(e) => setForm({ ...form, floor_id: e.target.value })}
                  required
                >
                  <option value="">Select a floor</option>
                  {floors.map((f) => (
                    <option key={f.id} value={f.id}>
                      {f.name}
                    </option>
                  ))}
                </select>
                <div className="quick-add">
                  <input placeholder="New floor name" value={newFloorName} onChange={(e) => setNewFloorName(e.target.value)} />
                  <input
                    placeholder="#"
                    type="number"
                    className="quick-add__number"
                    value={newFloorNumber}
                    onChange={(e) => setNewFloorNumber(e.target.value)}
                  />
                  <button type="button" onClick={handleQuickAddFloor}>Add</button>
                </div>
              </div>

              <div className="form-field">
                <label>Room type</label>
                <select
                  value={form.room_type_id}
                  onChange={(e) => setForm({ ...form, room_type_id: e.target.value })}
                  required
                >
                  <option value="">Select a type</option>
                  {roomTypes.map((t) => (
                    <option key={t.id} value={t.id}>
                      {t.name}
                    </option>
                  ))}
                </select>
                <div className="quick-add">
                  <input placeholder="New type name" value={newTypeName} onChange={(e) => setNewTypeName(e.target.value)} />
                  <input
                    placeholder="Rs/night"
                    type="number"
                    className="quick-add__number"
                    value={newTypePrice}
                    onChange={(e) => setNewTypePrice(e.target.value)}
                  />
                  <input
                    placeholder="Max"
                    type="number"
                    className="quick-add__number"
                    value={newTypeOccupancy}
                    onChange={(e) => setNewTypeOccupancy(e.target.value)}
                  />
                  <button type="button" onClick={handleQuickAddType}>Add</button>
                </div>
              </div>
            </div>

            <div className="form-field">
              <label>Description</label>
              <textarea
                rows={3}
                value={form.description}
                onChange={(e) => setForm({ ...form, description: e.target.value })}
                placeholder="A bright room facing the courtyard..."
              />
            </div>

            <div className="form-field">
              <label>Amenities</label>
              <div className="amenity-chips">
                {amenities.map((a) => (
                  <button
                    type="button"
                    key={a.id}
                    className={`amenity-chip ${form.amenity_ids.includes(a.id) ? 'amenity-chip--active' : ''}`}
                    onClick={() => toggleAmenity(a.id)}
                  >
                    {a.name}
                  </button>
                ))}
              </div>
              <div className="quick-add">
                <input placeholder="New amenity (e.g. Balcony)" value={newAmenityName} onChange={(e) => setNewAmenityName(e.target.value)} />
                <button type="button" onClick={handleQuickAddAmenity}>Add</button>
              </div>
            </div>

            <div className="room-form__actions">
              <button className="btn-primary" type="submit" disabled={submitting}>
                {submitting ? 'Saving...' : editingId ? 'Save changes' : 'Create room'}
              </button>
              <button type="button" className="btn-link" onClick={() => { setFormOpen(false); resetForm(); }}>
                Cancel
              </button>
            </div>
          </form>
        )}

        {loading && <p className="listing-status">Loading rooms...</p>}

        <div className="manage-rooms-list">
          {rooms.map((room) => (
            <div className="manage-room-card" key={room.id}>
              <div className="manage-room-card__image">
                {room.primary_image_url ? (
                  <img src={`${API_BASE}${room.primary_image_url}`} alt={`Room ${room.room_number}`} />
                ) : (
                  <div className="manage-room-card__image-placeholder">No photo</div>
                )}
                <label className="manage-room-card__upload">
                  {uploadingRoomId === room.id ? 'Uploading...' : 'Upload photo'}
                  <input
                    type="file"
                    accept="image/png, image/jpeg, image/webp"
                    hidden
                    disabled={uploadingRoomId === room.id}
                    onChange={(e) => e.target.files?.[0] && handleImageUpload(room.id, e.target.files[0])}
                  />
                </label>
              </div>

              <div className="manage-room-card__body">
                <div className="manage-room-card__top">
                  <h3>Room {room.room_number}</h3>
                  <span className={`manage-room-card__status manage-room-card__status--${room.availability_status.toLowerCase()}`}>
                    {room.availability_status.replace('_', ' ')}
                  </span>
                </div>
                <p className="manage-room-card__meta">
                  {room.room_type.name} - {room.floor.name} - Sleeps {room.capacity} - Rs.{room.price_per_night}/night
                </p>
                <div className="manage-room-card__actions">
                  <button onClick={() => openEditForm(room)}>Edit</button>
                  <button className="manage-room-card__deactivate" onClick={() => handleDeactivate(room)}>
                    Deactivate
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>

        {!loading && rooms.length === 0 && !formOpen && (
          <p className="listing-status">No rooms yet. Click "+ Add room" to create the first one.</p>
        )}
      </div>
    </div>
  );
}
