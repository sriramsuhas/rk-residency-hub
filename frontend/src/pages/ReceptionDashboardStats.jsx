import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import TopNav from '../components/TopNav';
import { analyticsApi } from '../api/analytics';
import './ReceptionDashboard.css';

export default function ReceptionDashboardStats() {
  const [data, setData] = useState(null);

  useEffect(() => {
    analyticsApi.reception().then((res) => setData(res.data.data));
  }, []);

  if (!data) return null;

  return (
    <div className="reception-stats">
      <div className="stat-card">
        <span className="stat-card__label">Expected check-ins today</span>
        <span className="stat-card__value">{data.todays_expected_checkins}</span>
      </div>
      <div className="stat-card">
        <span className="stat-card__label">Expected check-outs today</span>
        <span className="stat-card__value">{data.todays_expected_checkouts}</span>
      </div>
      <div className="stat-card">
        <span className="stat-card__label">Today's revenue</span>
        <span className="stat-card__value">₹{data.todays_revenue.toLocaleString('en-IN')}</span>
      </div>
      <div className="stat-card">
        <span className="stat-card__label">Awaiting payment</span>
        <span className="stat-card__value">{data.pending_bookings_count}</span>
      </div>
    </div>
  );
}
