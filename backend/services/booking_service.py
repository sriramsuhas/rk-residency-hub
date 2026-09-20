"""
Business logic for the booking engine: availability checks, booking creation
with conflict prevention, cancellation, and the reception check-in/check-out
workflow.
"""
from datetime import date, datetime, timezone

from sqlalchemy.orm import Session

from models.booking import Booking
from models.enums import AvailabilityStatus, BookingStatus, CleaningStatus
from repositories.audit_log_repository import AuditLogRepository
from repositories.booking_repository import BookingRepository
from repositories.room_repository import RoomRepository
from schemas.booking_schemas import BookingCreateRequest
from utils.email import send_email
from utils.email_templates import booking_cancellation_email
from utils.enum_utils import status_label
from utils.exceptions import NotFoundError, UnauthorizedError, ValidationAppError


class BookingService:
    def __init__(self, db: Session):
        self.db = db
        self.bookings = BookingRepository(db)
        self.rooms = RoomRepository(db)
        self.audit = AuditLogRepository(db)

    def check_availability(self, room_id: int, check_in: date, check_out: date) -> tuple[bool, str | None]:
        room = self.rooms.get_by_id(room_id)
        if room is None or not room.is_active:
            return False, "Room does not exist or is no longer active"
        if room.availability_status == AvailabilityStatus.OUT_OF_SERVICE.value:
            return False, "Room is currently out of service"
        if check_out <= check_in:
            return False, "Check-out date must be after check-in date"
        if self.bookings.has_overlap(room_id, check_in, check_out):
            return False, "Room is already booked for part of this date range"
        return True, None

    def create_booking(self, payload: BookingCreateRequest, customer_id: int) -> Booking:
        if payload.check_in_date < date.today():
            raise ValidationAppError("Check-in date cannot be in the past")

        room = self.rooms.get_by_id(payload.room_id)
        if room is None or not room.is_active:
            raise NotFoundError("Room not found")

        if payload.num_guests > room.capacity:
            raise ValidationAppError(f"This room sleeps a maximum of {room.capacity} guests")

        available, reason = self.check_availability(
            payload.room_id, payload.check_in_date, payload.check_out_date
        )
        if not available:
            raise ValidationAppError(reason or "Room is not available for the selected dates")

        nights = (payload.check_out_date - payload.check_in_date).days
        total_amount = float(room.price_per_night) * nights

        booking = Booking(
            customer_id=customer_id,
            room_id=payload.room_id,
            check_in_date=payload.check_in_date,
            check_out_date=payload.check_out_date,
            num_guests=payload.num_guests,
            status=BookingStatus.PENDING_PAYMENT,
            total_amount=total_amount,
            special_requests=payload.special_requests,
        )
        booking = self.bookings.create(booking)
        self.audit.log(
            action="BOOKING_CREATED", user_id=customer_id, entity_type="Booking", entity_id=booking.id
        )
        return self.bookings.get_by_id(booking.id)

    def get_booking(self, booking_id: int) -> Booking:
        booking = self.bookings.get_by_id(booking_id)
        if booking is None:
            raise NotFoundError("Booking not found")
        return booking

    def _assert_can_view(self, booking: Booking, requester_id: int, requester_role: str) -> None:
        is_owner = booking.customer_id == requester_id
        is_staff = requester_role in ("RECEPTION", "OWNER")
        if not (is_owner or is_staff):
            raise UnauthorizedError("You do not have access to this booking")

    def get_booking_for_viewer(self, booking_id: int, requester_id: int, requester_role: str) -> Booking:
        booking = self.get_booking(booking_id)
        self._assert_can_view(booking, requester_id, requester_role)
        return booking

    def list_my_bookings(self, customer_id: int, page: int, page_size: int, status_filter: str | None):
        return self.bookings.list_for_customer(customer_id, page, page_size, status_filter)

    def search_bookings(self, **kwargs):
        return self.bookings.search(**kwargs)

    def cancel_booking(self, booking_id: int, requester_id: int, requester_role: str, reason: str | None) -> Booking:
        booking = self.get_booking(booking_id)
        self._assert_can_view(booking, requester_id, requester_role)

        if booking.status not in (BookingStatus.PENDING_PAYMENT.value, BookingStatus.CONFIRMED.value):
            raise ValidationAppError(
                f"Only PENDING_PAYMENT or CONFIRMED bookings can be cancelled (this one is {status_label(booking.status)})"
            )

        booking.status = BookingStatus.CANCELLED
        booking.cancelled_at = datetime.now(timezone.utc)
        booking.cancellation_reason = reason
        self.bookings.update(booking)

        subject, body = booking_cancellation_email(
            booking.customer.full_name,
            booking.room.room_number,
            booking.check_in_date.isoformat(),
            booking.check_out_date.isoformat(),
        )
        send_email(booking.customer.email, subject, body)

        self.audit.log(
            action="BOOKING_CANCELLED", user_id=requester_id, entity_type="Booking", entity_id=booking.id
        )
        return self.get_booking(booking_id)

    def mark_confirmed(self, booking_id: int) -> Booking:
        """Called by PaymentService once a mock payment succeeds."""
        booking = self.get_booking(booking_id)
        if booking.status != BookingStatus.PENDING_PAYMENT.value:
            raise ValidationAppError(
                f"Only PENDING_PAYMENT bookings can be confirmed by payment (this one is {status_label(booking.status)})"
            )
        booking.status = BookingStatus.CONFIRMED
        self.bookings.update(booking)
        return self.get_booking(booking_id)

    def check_in(self, booking_id: int, actor_id: int) -> Booking:
        booking = self.get_booking(booking_id)
        if booking.status != BookingStatus.CONFIRMED.value:
            raise ValidationAppError(f"Only CONFIRMED bookings can be checked in (this one is {status_label(booking.status)})")

        booking.status = BookingStatus.CHECKED_IN
        booking.checked_in_at = datetime.now(timezone.utc)
        self.bookings.update(booking)

        room = self.rooms.get_by_id(booking.room_id)
        room.availability_status = AvailabilityStatus.BOOKED.value
        self.rooms.update(room)

        self.audit.log(action="BOOKING_CHECKED_IN", user_id=actor_id, entity_type="Booking", entity_id=booking.id)
        return self.get_booking(booking_id)

    def check_out(self, booking_id: int, actor_id: int) -> Booking:
        booking = self.get_booking(booking_id)
        if booking.status != BookingStatus.CHECKED_IN.value:
            raise ValidationAppError(
                f"Only CHECKED_IN bookings can be checked out (this one is {status_label(booking.status)})"
            )

        booking.status = BookingStatus.CHECKED_OUT
        booking.checked_out_at = datetime.now(timezone.utc)
        self.bookings.update(booking)

        room = self.rooms.get_by_id(booking.room_id)
        room.availability_status = AvailabilityStatus.AVAILABLE.value
        room.cleaning_status = CleaningStatus.DIRTY.value
        self.rooms.update(room)

        self.audit.log(action="BOOKING_CHECKED_OUT", user_id=actor_id, entity_type="Booking", entity_id=booking.id)
        return self.get_booking(booking_id)

    def assign_room(self, booking_id: int, new_room_id: int, actor_id: int) -> Booking:
        booking = self.get_booking(booking_id)
        if booking.status != BookingStatus.CONFIRMED.value:
            raise ValidationAppError("Can only reassign the room while the booking is CONFIRMED")

        new_room = self.rooms.get_by_id(new_room_id)
        if new_room is None or not new_room.is_active:
            raise NotFoundError("Target room not found")

        if self.bookings.has_overlap(
            new_room_id, booking.check_in_date, booking.check_out_date, exclude_booking_id=booking.id
        ):
            raise ValidationAppError("Target room is not available for this booking's dates")

        nights = (booking.check_out_date - booking.check_in_date).days
        booking.room_id = new_room_id
        booking.total_amount = float(new_room.price_per_night) * nights
        self.bookings.update(booking)

        self.audit.log(
            action="BOOKING_ROOM_REASSIGNED", user_id=actor_id, entity_type="Booking", entity_id=booking.id
        )
        return self.get_booking(booking_id)
