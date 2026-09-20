import { useCallback, useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import TopNav from '../components/TopNav';
import { bookingsApi } from '../api/bookings';
import { paymentsApi } from '../api/payments';
import { reviewsApi } from '../api/reviews';
import '../styles/status.css';
import '../styles/forms.css';
import './MyBookings.css';

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

const STATUS_LABEL = {
  PENDING_PAYMENT: 'Awaiting payment',
  CONFIRMED: 'Confirmed',
  CHECKED_IN: 'Checked in',
  CHECKED_OUT: 'Checked out',
  CANCELLED: 'Cancelled',
};

export default function MyBookings() {
  const [bookings, setBookings] = useState([]);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState('');
  const [cancellingId, setCancellingId] = useState(null);
  const [payingId, setPayingId] = useState(null);
  const [downloadingId, setDownloadingId] = useState(null);
  const [error, setError] = useState('');

  const [reviewingId, setReviewingId] = useState(null);
  const [reviewRating, setReviewRating] = useState(5);
  const [reviewComment, setReviewComment] = useState('');
  const [submittingReview, setSubmittingReview] = useState(false);
  const [reviewedBookingIds, setReviewedBookingIds] = useState([]);

  const load = useCallback(() => {
    setLoading(true);
    bookingsApi
      .myBookings({ status: statusFilter || undefined, page_size: 50 })
      .then((res) => setBookings(res.data.data.items))
      .catch(() => setError('Could not load your bookings.'))
      .finally(() => setLoading(false));
  }, [statusFilter]);

  useEffect(() => {
    load();
  }, [load]);

  useEffect(() => {
    reviewsApi.myReviews({ page_size: 50 }).then((res) => {
      setReviewedBookingIds(res.data.data.items.map((r) => r.booking_id));
    });
  }, []);

  async function handleCancel(bookingId) {
    setCancellingId(bookingId);
    try {
      await bookingsApi.cancel(bookingId, 'Cancelled by guest');
      load();
    } catch (err) {
      setError(err.response?.data?.message || 'Could not cancel this booking.');
    } finally {
      setCancellingId(null);
    }
  }

  async function handlePay(bookingId) {
    setPayingId(bookingId);
    setError('');
    try {
      await paymentsApi.pay(bookingId, 'CARD');
      load();
    } catch (err) {
      setError(err.response?.data?.message || 'Payment could not be completed.');
    } finally {
      setPayingId(null);
    }
  }

  async function handleDownloadInvoice(bookingId, invoiceNumberHint) {
    setDownloadingId(bookingId);
    setError('');
    try {
      await paymentsApi.downloadInvoicePdf(bookingId, invoiceNumberHint);
    } catch (err) {
      setError('Invoice is not available yet.');
    } finally {
      setDownloadingId(null);
    }
  }

  function openReviewForm(bookingId) {
    setReviewingId(bookingId);
    setReviewRating(5);
    setReviewComment('');
  }

  async function handleSubmitReview(bookingId) {
    setSubmittingReview(true);
    setError('');
    try {
      await reviewsApi.create(bookingId, reviewRating, reviewComment || undefined);
      setReviewedBookingIds((prev) => [...prev, bookingId]);
      setReviewingId(null);
    } catch (err) {
      setError(err.response?.data?.message || 'Could not submit your review.');
    } finally {
      setSubmittingReview(false);
    }
  }

  return (
    <div>
      <TopNav />
      <div className="mybookings-page">
        <div className="mybookings-header">
          <h1>My bookings</h1>
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
        {!loading && bookings.length === 0 && (
          <p className="listing-status">
            No bookings yet. <Link to="/">Browse rooms</Link> to make your first one.
          </p>
        )}

        <div className="booking-list">
          {bookings.map((b) => (
            <div className="booking-row" key={b.id}>
              <div className="booking-row__image">
                {b.room.primary_image_url ? (
                  <img src={`${API_BASE}${b.room.primary_image_url}`} alt="" />
                ) : (
                  <div className="booking-row__image-placeholder" />
                )}
              </div>
              <div className="booking-row__body">
                <div className="booking-row__top">
                  <h3>
                    <Link to={`/rooms/${b.room.id}`}>Room {b.room.room_number}</Link>
                  </h3>
                  <span className={`booking-status booking-status--${b.status.toLowerCase()}`}>
                    {STATUS_LABEL[b.status]}
                  </span>
                </div>
                <p className="booking-row__dates">
                  {b.check_in_date} → {b.check_out_date} · {b.num_guests} guest{b.num_guests === 1 ? '' : 's'}
                </p>
                <p className="booking-row__total">₹{b.total_amount} total</p>
                {b.status === 'CANCELLED' && b.cancellation_reason && (
                  <p className="booking-row__cancel-reason">Reason: {b.cancellation_reason}</p>
                )}
                {b.status === 'CHECKED_OUT' && reviewedBookingIds.includes(b.id) && (
                  <p className="booking-row__reviewed">✓ You reviewed this stay</p>
                )}
                {b.status === 'CHECKED_OUT' && !reviewedBookingIds.includes(b.id) && reviewingId === b.id && (
                  <div className="booking-row__review-form">
                    <div className="form-field">
                      <label>Rating</label>
                      <select value={reviewRating} onChange={(e) => setReviewRating(Number(e.target.value))}>
                        {[5, 4, 3, 2, 1].map((n) => (
                          <option key={n} value={n}>
                            {'★'.repeat(n)}{'☆'.repeat(5 - n)}
                          </option>
                        ))}
                      </select>
                    </div>
                    <div className="form-field">
                      <label>Comment (optional)</label>
                      <textarea
                        rows={2}
                        value={reviewComment}
                        onChange={(e) => setReviewComment(e.target.value)}
                        placeholder="How was your stay?"
                      />
                    </div>
                    <div className="booking-row__review-form-actions">
                      <button
                        className="btn-primary"
                        onClick={() => handleSubmitReview(b.id)}
                        disabled={submittingReview}
                      >
                        {submittingReview ? 'Submitting…' : 'Submit review'}
                      </button>
                      <button className="btn-link" onClick={() => setReviewingId(null)}>
                        Cancel
                      </button>
                    </div>
                  </div>
                )}
              </div>
              <div className="booking-row__actions">
                {b.status === 'PENDING_PAYMENT' && (
                  <button
                    className="booking-row__pay-btn"
                    onClick={() => handlePay(b.id)}
                    disabled={payingId === b.id}
                  >
                    {payingId === b.id ? 'Paying…' : 'Pay now'}
                  </button>
                )}
                {['CONFIRMED', 'CHECKED_IN', 'CHECKED_OUT'].includes(b.status) && (
                  <button
                    className="booking-row__invoice-btn"
                    onClick={() => handleDownloadInvoice(b.id, `booking-${b.id}-invoice`)}
                    disabled={downloadingId === b.id}
                  >
                    {downloadingId === b.id ? 'Downloading…' : 'Invoice'}
                  </button>
                )}
                {b.status === 'CHECKED_OUT' && !reviewedBookingIds.includes(b.id) && reviewingId !== b.id && (
                  <button className="booking-row__invoice-btn" onClick={() => openReviewForm(b.id)}>
                    Leave a review
                  </button>
                )}
                {(b.status === 'CONFIRMED' || b.status === 'PENDING_PAYMENT') && (
                  <button
                    className="booking-row__cancel-btn"
                    onClick={() => handleCancel(b.id)}
                    disabled={cancellingId === b.id}
                  >
                    {cancellingId === b.id ? 'Cancelling…' : 'Cancel'}
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
