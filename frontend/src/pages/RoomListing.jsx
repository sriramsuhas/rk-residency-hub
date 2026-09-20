import { useCallback, useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import TopNav from '../components/TopNav';
import { roomsApi } from '../api/rooms';
import './RoomListing.css';

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

export default function RoomListing() {
  const [rooms, setRooms] = useState([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const [floors, setFloors] = useState([]);
  const [roomTypes, setRoomTypes] = useState([]);
  const [amenities, setAmenities] = useState([]);

  const [filters, setFilters] = useState({
    search: '',
    floor_id: '',
    room_type_id: '',
    min_price: '',
    max_price: '',
    capacity: '',
    sort_by: 'room_number',
  });
  const [selectedAmenityIds, setSelectedAmenityIds] = useState([]);
  const [page, setPage] = useState(1);
  const pageSize = 9;

  useEffect(() => {
    Promise.all([roomsApi.floors(), roomsApi.roomTypes(), roomsApi.amenities()]).then(
      ([floorsRes, typesRes, amenitiesRes]) => {
        setFloors(floorsRes.data.data);
        setRoomTypes(typesRes.data.data);
        setAmenities(amenitiesRes.data.data);
      }
    );
  }, []);

  const loadRooms = useCallback(() => {
    setLoading(true);
    setError('');
    const params = { ...filters, page, page_size: pageSize, amenity_ids: selectedAmenityIds };
    roomsApi
      .search(params)
      .then((res) => {
        setRooms(res.data.data.items);
        setTotal(res.data.data.total);
      })
      .catch(() => setError('Could not load rooms. Please try again.'))
      .finally(() => setLoading(false));
  }, [filters, page, selectedAmenityIds]);

  useEffect(() => {
    loadRooms();
  }, [loadRooms]);

  function updateFilter(field) {
    return (e) => {
      setPage(1);
      setFilters((prev) => ({ ...prev, [field]: e.target.value }));
    };
  }

  function toggleAmenity(id) {
    setPage(1);
    setSelectedAmenityIds((prev) => (prev.includes(id) ? prev.filter((a) => a !== id) : [...prev, id]));
  }

  const totalPages = Math.max(1, Math.ceil(total / pageSize));

  return (
    <div>
      <TopNav />
      <div className="listing-page">
        <div className="listing-header">
          <h1 className="listing-title">Browse rooms</h1>
          <p className="listing-subtitle">{total} room{total === 1 ? '' : 's'} available</p>
        </div>

        <div className="listing-layout">
          <aside className="listing-filters">
            <div className="filter-group">
              <label>Search</label>
              <input
                type="text"
                placeholder="Room number or description"
                value={filters.search}
                onChange={updateFilter('search')}
              />
            </div>

            <div className="filter-group">
              <label>Floor</label>
              <select value={filters.floor_id} onChange={updateFilter('floor_id')}>
                <option value="">Any floor</option>
                {floors.map((f) => (
                  <option key={f.id} value={f.id}>
                    {f.name}
                  </option>
                ))}
              </select>
            </div>

            <div className="filter-group">
              <label>Room type</label>
              <select value={filters.room_type_id} onChange={updateFilter('room_type_id')}>
                <option value="">Any type</option>
                {roomTypes.map((rt) => (
                  <option key={rt.id} value={rt.id}>
                    {rt.name}
                  </option>
                ))}
              </select>
            </div>

            <div className="filter-group filter-group--row">
              <div>
                <label>Min price</label>
                <input type="number" min="0" value={filters.min_price} onChange={updateFilter('min_price')} />
              </div>
              <div>
                <label>Max price</label>
                <input type="number" min="0" value={filters.max_price} onChange={updateFilter('max_price')} />
              </div>
            </div>

            <div className="filter-group">
              <label>Guests</label>
              <input type="number" min="1" value={filters.capacity} onChange={updateFilter('capacity')} />
            </div>

            {amenities.length > 0 && (
              <div className="filter-group">
                <label>Amenities</label>
                <div className="amenity-chips">
                  {amenities.map((a) => (
                    <button
                      key={a.id}
                      type="button"
                      className={`amenity-chip ${selectedAmenityIds.includes(a.id) ? 'amenity-chip--active' : ''}`}
                      onClick={() => toggleAmenity(a.id)}
                    >
                      {a.name}
                    </button>
                  ))}
                </div>
              </div>
            )}

            <div className="filter-group">
              <label>Sort by</label>
              <select value={filters.sort_by} onChange={updateFilter('sort_by')}>
                <option value="room_number">Room number</option>
                <option value="price_asc">Price: low to high</option>
                <option value="price_desc">Price: high to low</option>
              </select>
            </div>
          </aside>

          <section className="listing-results">
            {error && <div className="listing-error">{error}</div>}
            {loading && <p className="listing-status">Loading rooms…</p>}
            {!loading && rooms.length === 0 && !error && (
              <p className="listing-status">No rooms match your filters.</p>
            )}

            <div className="room-grid">
              {rooms.map((room) => (
                <Link to={`/rooms/${room.id}`} key={room.id} className="room-card">
                  <div className="room-card__image">
                    {room.primary_image_url ? (
                      <img src={`${API_BASE}${room.primary_image_url}`} alt={`Room ${room.room_number}`} />
                    ) : (
                      <div className="room-card__image-placeholder">No photo yet</div>
                    )}
                    <span className={`room-card__status room-card__status--${room.availability_status.toLowerCase()}`}>
                      {room.availability_status.replace('_', ' ')}
                    </span>
                  </div>
                  <div className="room-card__body">
                    <div className="room-card__row">
                      <h3>Room {room.room_number}</h3>
                      <span className="room-card__price">₹{room.price_per_night}<small>/night</small></span>
                    </div>
                    <p className="room-card__meta">
                      {room.room_type.name} · {room.floor.name} · Sleeps {room.capacity}
                    </p>
                  </div>
                </Link>
              ))}
            </div>

            {totalPages > 1 && (
              <div className="pagination">
                <button disabled={page <= 1} onClick={() => setPage((p) => p - 1)}>
                  Previous
                </button>
                <span>
                  Page {page} of {totalPages}
                </span>
                <button disabled={page >= totalPages} onClick={() => setPage((p) => p + 1)}>
                  Next
                </button>
              </div>
            )}
          </section>
        </div>
      </div>
    </div>
  );
}
