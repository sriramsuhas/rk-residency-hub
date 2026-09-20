import { useEffect, useState } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';
import TopNav from '../components/TopNav';
import { roomsApi } from '../api/rooms';
import { bookingsApi } from '../api/bookings';
import { paymentsApi } from '../api/payments';
import { reviewsApi } from '../api/reviews';
import { useAuth } from '../context/AuthContext';
import '../styles/forms.css';
import './RoomDetails.css';

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

function todayIso() {
  return new Date().toISOString().slice(0, 10);
}

function addDaysIso(iso, days) {
  const d = new Date(iso);
  d.setDate(d.getDate() + days);
  return d.toISOString().slice(0, 10);
}

export default function RoomDetails() {
  const { id } = useParams();
  const { user } = useAuth();
  const navigate = useNavigate();
  const [room, setRoom] = useState(null);
  const [error, setError] = useState('');
  const [activeImage, setActiveImage] = useState(0);

  const [checkIn, setCheckIn] = useState(todayIso());
  const [checkOut, setCheckOut] = useState(addDaysIso(todayIso(), 1));
  const [guests, setGuests] = useState(1);
  const [availability, setAvailability] = useState(null);
  const [checkingAvailability, setCheckingAvailability] = useState(false);
  const [bookingError, setBookingError] = useState('');
  const [bookingSuccess, setBookingSuccess] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  const [pendingBookingId, setPendingBookingId] = useState(null);
  const [paymentMethod, setPaymentMethod] = useState('CARD');
  const [paying, setPaying] = useState(false);
  const [paymentError, setPaymentError] = useState('');
  const [paid, setPaid] = useState(false);

  const [reviews, setReviews] = useState([]);
  const [averageRating, setAverageRating] = useState(null);
  const [reviewCount, setReviewCount] = useState(0);

  useEffect(() => {
    setRoom(null);
    setError('');
    roomsApi
      .getById(id)
      .then((res) => {
        setRoom(res.data.data);
        setActiveImage(0);
        setGuests(1);
        setPendingBookingId(null);
        setPaid(false);
        setBookingSuccess(false);
        setBookingError('');
        setPaymentError('');
      })
      .catch(() => setError('This room could not be found.'));

    reviewsApi.forRoom(id, { page_size: 20 }).then((res) => {
      setReviews(res.data.data.items);
      setAverageRating(res.data.data.average_rating);
      setReviewCount(res.data.data.total);
    });
  }, [id]);

  useEffect(() => {
    if (!room || !checkIn || !checkOut || checkOut <= checkIn) {
      setAvailability(null);
      return;
    }
    setCheckingAvailability(true);
    bookingsApi
      .checkAvailability(id, checkIn, checkOut)
      .then((res) => setAvailability(res.data.data))
      .catch(() => setAvailability(null))
      .finally(() => setCheckingAvailability(false));
  }, [id, room, checkIn, checkOut]);

  async function handleBook() {
    setBookingError('');
    setBookingSuccess(false);

    if (!user) {
      navigate('/login', { state: { from: `/rooms/${id}` } });
      return;
    }

    setSubmitting(true);
    try {
      const res = await bookingsApi.create({
        room_id: Number(id),
        check_in_date: checkIn,
        check_out_date: checkOut,
        num_guests: Number(guests),
      });
      setPendingBookingId(res.data.data.id);
    } catch (err) {
      setBookingError(err.response?.data?.message || 'Could not complete the booking. Please try again.');
    } finally {
      setSubmitting(false);
    }
  }

  async function handlePay() {
    setPaymentError('');
    setPaying(true);
    try {
      await paymentsApi.pay(pendingBookingId, paymentMethod);
      setPaid(true);
      setBookingSuccess(true);
    } catch (err) {
      setPaymentError(err.response?.data?.message || 'Payment could not be completed. Please try again.');
    } finally {
      setPaying(false);
    }
  }

  const nights = checkIn && checkOut && checkOut > checkIn
    ? Math.round((new Date(checkOut) - new Date(checkIn)) / 86400000)
    : 0;
  const totalPrice = room ? nights * room.price_per_night : 0;
  const canBook = room && room.availability_status !== 'OUT_OF_SERVICE' && availability?.available && nights > 0;

  return (
    <div>
      <TopNav />
      <div className="details-page">
        <Link to="/" className="details-back">
          ← Back to rooms
        </Link>

        {error && <p className="listing-status">{error}</p>}

        {room && (
          <div className="details-layout">
            <div>
              <div className="details-gallery">
                {room.images.length > 0 ? (
                  <img
                    src={`${API_BASE}${room.images[activeImage].image_url}`}
                    alt={`Room ${room.room_number}`}
                  />
                ) : (
                  <div className="details-gallery__placeholder">No photos yet</div>
                )}
              </div>
              {room.images.length > 1 && (
                <div className="details-thumbs">
                  {room.images.map((img, i) => (
                    <button
                      key={img.id}
                      className={`details-thumb ${i === activeImage ? 'details-thumb--active' : ''}`}
                      onClick={() => setActiveImage(i)}
                    >
                      <img src={`${API_BASE}${img.image_url}`} alt="" />
                    </button>
                  ))}
                </div>
              )}

              {room.description && <p className="details-description">{room.description}</p>}

              {room.amenities.length > 0 && (
                <div className="details-amenities">
                  <h2>Amenities</h2>
                  <div className="details-amenities__list">
                    {room.amenities.map((a) => (
                      <span key={a.id} className="details-amenity">
                        {a.name}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              <div className="details-reviews">
                <h2>Reviews {reviewCount > 0 && `(${reviewCount})`}</h2>
                {reviews.length === 0 && <p className="details-reviews__empty">No reviews yet.</p>}
                {reviews.map((r) => (
                  <div className="review-card" key={r.id}>
                    <div className="review-card__top">
                      <span className="review-card__stars">{'★'.repeat(r.rating)}{'☆'.repeat(5 - r.rating)}</span>
                      <span className="review-card__author">{r.customer.full_name}</span>
                    </div>
                    {r.comment && <p className="review-card__comment">{r.comment}</p>}
                  </div>
                ))}
              </div>
            </div>

            <div className="details-info">
              <span className={`details-status details-status--${room.availability_status.toLowerCase()}`}>
                {room.availability_status.replace('_', ' ')}
              </span>
              <h1 className="details-title">Room {room.room_number}</h1>
              {averageRating !== null && (
                <p className="details-rating">
                  ★ {averageRating} <span>({reviewCount} review{reviewCount === 1 ? '' : 's'})</span>
                </p>
              )}
              <p className="details-meta">
                {room.room_type.name} · {room.floor.name} · Sleeps {room.capacity}
              </p>
              <p className="details-price">
                ₹{room.price_per_night} <span>/ night</span>
              </p>

              <div className="booking-widget">
                {!pendingBookingId && (
                  <>
                    <div className="booking-widget__row">
                      <div className="form-field">
                        <label>Check-in</label>
                        <input
                          type="date"
                          min={todayIso()}
                          value={checkIn}
                          onChange={(e) => {
                            setCheckIn(e.target.value);
                            if (e.target.value >= checkOut) setCheckOut(addDaysIso(e.target.value, 1));
                          }}
                        />
                      </div>
                      <div className="form-field">
                        <label>Check-out</label>
                        <input
                          type="date"
                          min={addDaysIso(checkIn, 1)}
                          value={checkOut}
                          onChange={(e) => setCheckOut(e.target.value)}
                        />
                      </div>
                    </div>

                    <div className="form-field">
                      <label>Guests</label>
                      <input
                        type="number"
                        min={1}
                        max={room.capacity}
                        value={guests}
                        onChange={(e) => setGuests(e.target.value)}
                      />
                    </div>

                    {checkingAvailability && <p className="booking-widget__hint">Checking availability…</p>}
                    {!checkingAvailability && availability && !availability.available && (
                      <div className="alert alert-error">{availability.reason || 'Not available for these dates.'}</div>
                    )}
                    {!checkingAvailability && availability?.available && nights > 0 && (
                      <p className="booking-widget__total">
                        {nights} night{nights === 1 ? '' : 's'} · <strong>₹{totalPrice}</strong> total
                      </p>
                    )}

                    {bookingError && <div className="alert alert-error">{bookingError}</div>}

                    <button
                      className="btn-primary details-book-btn"
                      disabled={!canBook || submitting || Number(guests) > room.capacity}
                      onClick={handleBook}
                    >
                      {submitting ? 'Reserving…' : user ? 'Reserve this room' : 'Sign in to book'}
                    </button>
                  </>
                )}

                {pendingBookingId && !paid && (
                  <>
                    <p className="booking-widget__hint">
                      Reserved — {nights} night{nights === 1 ? '' : 's'}, <strong>₹{totalPrice}</strong> total.
                      Complete payment to confirm.
                    </p>
                    <div className="form-field">
                      <label>Payment method</label>
                      <select value={paymentMethod} onChange={(e) => setPaymentMethod(e.target.value)}>
                        <option value="CARD">Card</option>
                        <option value="UPI">UPI</option>
                        <option value="CASH">Cash (pay at desk)</option>
                      </select>
                    </div>
                    {paymentError && <div className="alert alert-error">{paymentError}</div>}
                    <button className="btn-primary details-book-btn" onClick={handlePay} disabled={paying}>
                      {paying ? 'Processing payment…' : `Pay ₹${totalPrice}`}
                    </button>
                  </>
                )}

                {bookingSuccess && (
                  <div className="alert alert-success">
                    Booking confirmed! View it under{' '}
                    <Link to="/my-bookings">My Bookings</Link>.
                  </div>
                )}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

