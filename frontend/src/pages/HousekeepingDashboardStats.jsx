import { useEffect, useState } from 'react';
import { analyticsApi } from '../api/analytics';
import './HousekeepingDashboardStats.css';

export default function HousekeepingDashboardStats() {
  const [data, setData] = useState(null);

  useEffect(() => {
    analyticsApi.housekeeping().then((res) => setData(res.data.data));
  }, []);

  if (!data) return null;

  return (
    <div className="hk-stats">
      <div className="hk-stat-card">
        <span className="hk-stat-card__label">Rooms needing cleaning</span>
        <span className="hk-stat-card__value">{data.pending_cleaning_count}</span>
      </div>
      <div className="hk-stat-card">
        <span className="hk-stat-card__label">Pending maintenance</span>
        <span className="hk-stat-card__value">{data.pending_maintenance_count}</span>
      </div>
      <div className="hk-stat-card">
        <span className="hk-stat-card__label">Completed today</span>
        <span className="hk-stat-card__value">{data.completed_today_count}</span>
      </div>

      {data.pending_cleaning_rooms.length > 0 && (
        <div className="hk-stats__rooms">
          <span className="hk-stats__rooms-label">Rooms to clean:</span>
          {data.pending_cleaning_rooms.map((r) => (
            <span key={r.room_id} className="hk-stats__room-chip">
              {r.room_number} ({r.floor_name})
            </span>
          ))}
        </div>
      )}
    </div>
  );
}
