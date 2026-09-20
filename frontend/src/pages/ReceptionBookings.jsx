import { useCallback, useEffect, useState } from 'react';
import TopNav from '../components/TopNav';
import { bookingsApi } from '../api/bookings';
import { paymentsApi } from '../api/payments';
import '../styles/status.css';
import ReceptionDashboardStats from './ReceptionDashboardStats';
import './ReceptionBookings.css';

export default function ReceptionBookings() {
  const [bookings, setBookings] = useState([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [actingId, setActingId] = useState(null);

  const load = useCallback(() => {
    setLoading(true);
    setError('');
    bookingsApi
      .searchAll({ status: statusFilter || undefined, page_size: 50 })
      .then((res) => {
        setBookings(res.data.data.items);
        setTotal(res.data.data.total);
      })
      .catch(() => setError('Could not load bookings.'))
      .finally(() => setLoading(false));
  }, [statusFilter]);

  useEffect(() => {
    load();
  }, [load]);

  async function handleAction(bookingId, action) {
    setActingId(bookingId);
    setError('');
    try {
      if (action === 'check-in') await bookingsApi.checkIn(bookingId);
      if (action === 'check-out') await bookingsApi.checkOut(bookingId);
      load();
    } catch (err) {
      setError(err.response?.data?.message || 'That action could not be completed.');
    } finally {
      setActingId(null);
    }
  }

  async function handleRefund(bookingId) {
    setActingId(bookingId);
    setError('');
    try {
      const invoice = await paymentsApi.getInvoice(bookingId);
      await paymentsApi.refund(invoice.data.data.payment_id, 'Refunded by reception');
      load();
    } catch (err) {
      setError(
        err.response?.status === 404
          ? 'This booking was never paid, so there is nothing to refund.'
          : err.response?.data?.message || 'Refund could not be processed.'
      );
    } finally {
      setActingId(null);
    }
  }

  return (
    <div>
      <TopNav />
      <div className="reception-page">
        <ReceptionDashboardStats />
        <div className="reception-header">
          <div>
            <h1>Bookings</h1>
            <p>{total} booking{total === 1 ? '' : 's'}</p>
          </div>
          <select value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)}>
            <option value="">All statuses</option>
            <option value="PENDING_PAYMENT">Awaiting payment</option>
            <option value="CONFIRMED">Confirmed</option>
            <option value="CHECKED_IN">Checked in</option>
            <option value="CHECKED_OUT">Checked out</option>
            <option value="CANCELLED">Cancelled</option>
          </select>
        </div>

        {error && <div className="alert alert-error">{error}</div>}
        {loading && <p className="listing-status">Loading…</p>}

        {!loading && (
          <table className="reception-table">
            <thead>
              <tr>
                <th>Guest</th>
                <th>Room</th>
                <th>Dates</th>
                <th>Guests</th>
                <th>Status</th>
                <th>Total</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {bookings.map((b) => (
                <tr key={b.id}>
                  <td>{b.customer.full_name}</td>
                  <td>{b.room.room_number}</td>
                  <td>{b.check_in_date} → {b.check_out_date}</td>
                  <td>{b.num_guests}</td>
                  <td>
                    <span className={`booking-status booking-status--${b.status.toLowerCase()}`}>
                      {b.status.replace('_', ' ')}
                    </span>
                  </td>
                  <td>₹{b.total_amount}</td>
                  <td className="reception-table__actions">
                    {b.status === 'CONFIRMED' && (
                      <button
                        onClick={() => handleAction(b.id, 'check-in')}
                        disabled={actingId === b.id}
                      >
                        Check in
                      </button>
                    )}
                    {b.status === 'CHECKED_IN' && (
                      <button
                        onClick={() => handleAction(b.id, 'check-out')}
                        disabled={actingId === b.id}
                      >
                        Check out
                      </button>
                    )}
                    {b.status === 'CANCELLED' && (
                      <button onClick={() => handleRefund(b.id)} disabled={actingId === b.id}>
                        {actingId === b.id ? 'Processing…' : 'Refund'}
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}

        {!loading && bookings.length === 0 && <p className="listing-status">No bookings found.</p>}
      </div>
    </div>
  );
}
