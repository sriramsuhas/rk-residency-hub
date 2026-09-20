import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { Area, AreaChart, Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';
import TopNav from '../components/TopNav';
import { analyticsApi } from '../api/analytics';
import './OwnerDashboard.css';

function formatDate(iso) {
  const d = new Date(iso);
  return d.toLocaleDateString('en-IN', { month: 'short', day: 'numeric' });
}

export default function OwnerDashboard() {
  const [data, setData] = useState(null);
  const [error, setError] = useState('');

  useEffect(() => {
    analyticsApi
      .owner()
      .then((res) => setData(res.data.data))
      .catch(() => setError('Could not load dashboard data.'));
  }, []);

  if (error) return <div><TopNav /><p className="listing-status">{error}</p></div>;
  if (!data) return <div><TopNav /><p className="listing-status">Loading dashboard…</p></div>;

  const revenueChartData = data.daily_revenue_trend.map((p) => ({ date: formatDate(p.date), value: p.value }));
  const bookingChartData = data.booking_trend.map((p) => ({ date: formatDate(p.date), value: p.value }));

  return (
    <div>
      <TopNav />
      <div className="owner-dash">
        <div className="owner-dash__title-row">
          <h1>Owner overview</h1>
          <div className="owner-dash__title-actions">
            <Link to="/manage-rooms" className="btn-primary owner-dash__manage-btn">
              + Manage rooms
            </Link>
            <Link to="/manage-users" className="owner-dash__manage-link">
              Manage users
            </Link>
          </div>
        </div>

        <div className="owner-dash__stats">
          <div className="stat-card">
            <span className="stat-card__label">Total revenue</span>
            <span className="stat-card__value">₹{data.total_revenue.toLocaleString('en-IN')}</span>
          </div>
          <div className="stat-card">
            <span className="stat-card__label">Revenue (30d)</span>
            <span className="stat-card__value">₹{data.revenue_last_30_days.toLocaleString('en-IN')}</span>
          </div>
          <div className="stat-card">
            <span className="stat-card__label">Occupancy rate</span>
            <span className="stat-card__value">{data.occupancy_rate}%</span>
            <span className="stat-card__sub">{data.occupied_room_count} of {data.active_room_count} rooms</span>
          </div>
          <div className="stat-card">
            <span className="stat-card__label">Pending maintenance</span>
            <span className="stat-card__value">{data.maintenance_stats.pending_count + data.maintenance_stats.assigned_count + data.maintenance_stats.in_progress_count}</span>
          </div>
        </div>

        <div className="owner-dash__charts">
          <div className="chart-card">
            <h2>Revenue, last 30 days</h2>
            {revenueChartData.length === 0 ? (
              <p className="chart-card__empty">No revenue yet.</p>
            ) : (
              <ResponsiveContainer width="100%" height={220}>
                <AreaChart data={revenueChartData}>
                  <defs>
                    <linearGradient id="revenueGradient" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="0%" stopColor="#4B5D45" stopOpacity={0.35} />
                      <stop offset="100%" stopColor="#4B5D45" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="#E4DDD0" />
                  <XAxis dataKey="date" tick={{ fontSize: 11, fill: '#8A8477' }} />
                  <YAxis tick={{ fontSize: 11, fill: '#8A8477' }} />
                  <Tooltip formatter={(v) => [`₹${v}`, 'Revenue']} />
                  <Area type="monotone" dataKey="value" stroke="#4B5D45" fill="url(#revenueGradient)" strokeWidth={2} />
                </AreaChart>
              </ResponsiveContainer>
            )}
          </div>

          <div className="chart-card">
            <h2>Bookings, last 30 days</h2>
            {bookingChartData.length === 0 ? (
              <p className="chart-card__empty">No bookings yet.</p>
            ) : (
              <ResponsiveContainer width="100%" height={220}>
                <BarChart data={bookingChartData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#E4DDD0" />
                  <XAxis dataKey="date" tick={{ fontSize: 11, fill: '#8A8477' }} />
                  <YAxis tick={{ fontSize: 11, fill: '#8A8477' }} allowDecimals={false} />
                  <Tooltip />
                  <Bar dataKey="value" fill="#A97D50" radius={[3, 3, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            )}
          </div>
        </div>

        <div className="owner-dash__lists">
          <div className="list-card">
            <h2>Popular rooms</h2>
            {data.popular_rooms.length === 0 && <p className="chart-card__empty">No bookings yet.</p>}
            {data.popular_rooms.map((r) => (
              <div className="list-card__row" key={r.room_id}>
                <span>Room {r.room_number}</span>
                <span className="list-card__count">{r.booking_count} booking{r.booking_count === 1 ? '' : 's'}</span>
              </div>
            ))}
          </div>

          <div className="list-card">
            <h2>Maintenance snapshot</h2>
            <div className="list-card__row">
              <span>Pending</span>
              <span className="list-card__count">{data.maintenance_stats.pending_count}</span>
            </div>
            <div className="list-card__row">
              <span>Assigned</span>
              <span className="list-card__count">{data.maintenance_stats.assigned_count}</span>
            </div>
            <div className="list-card__row">
              <span>In progress</span>
              <span className="list-card__count">{data.maintenance_stats.in_progress_count}</span>
            </div>
            <div className="list-card__row">
              <span>Completed</span>
              <span className="list-card__count">{data.maintenance_stats.completed_count}</span>
            </div>
            {data.maintenance_stats.most_frequent_category && (
              <p className="list-card__note">
                Most frequent issue: {data.maintenance_stats.most_frequent_category}
                {data.maintenance_stats.average_resolution_hours != null &&
                  ` · avg. resolution ${data.maintenance_stats.average_resolution_hours}h`}
              </p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
