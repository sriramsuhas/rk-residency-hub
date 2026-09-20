"""Direct database access for bookings, including the date-overlap conflict query."""
from datetime import date

from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from models.booking import Booking
from models.enums import BookingStatus


class BookingRepository:
    def __init__(self, db: Session):
        self.db = db

    def _with_relations(self, stmt):
        return stmt.options(
            joinedload(Booking.room),
            joinedload(Booking.customer),
        )

    def get_by_id(self, booking_id: int) -> Booking | None:
        stmt = self._with_relations(select(Booking).where(Booking.id == booking_id))
        return self.db.execute(stmt).unique().scalar_one_or_none()

    def create(self, booking: Booking) -> Booking:
        self.db.add(booking)
        self.db.commit()
        self.db.refresh(booking)
        return booking

    def update(self, booking: Booking) -> Booking:
        self.db.commit()
        self.db.refresh(booking)
        return booking

    def has_overlap(
        self, room_id: int, check_in: date, check_out: date, exclude_booking_id: int | None = None
    ) -> bool:
        """
        True if an active (CONFIRMED/CHECKED_IN) booking for this room overlaps
        the given date range. Two ranges [a_in, a_out) and [b_in, b_out) overlap
        iff a_in < b_out AND b_in < a_out.
        """
        stmt = select(Booking.id).where(
            Booking.room_id == room_id,
            Booking.status.in_(
                [
                    BookingStatus.PENDING_PAYMENT.value,
                    BookingStatus.CONFIRMED.value,
                    BookingStatus.CHECKED_IN.value,
                ]
            ),
            Booking.check_in_date < check_out,
            Booking.check_out_date > check_in,
        )
        if exclude_booking_id is not None:
            stmt = stmt.where(Booking.id != exclude_booking_id)
        return self.db.execute(stmt.limit(1)).scalar_one_or_none() is not None

    def list_for_customer(
        self, customer_id: int, page: int, page_size: int, status_filter: str | None = None
    ) -> tuple[list[Booking], int]:
        stmt = self._with_relations(select(Booking).where(Booking.customer_id == customer_id))
        count_stmt = select(func.count()).select_from(Booking).where(Booking.customer_id == customer_id)

        if status_filter:
            stmt = stmt.where(Booking.status == status_filter)
            count_stmt = count_stmt.where(Booking.status == status_filter)

        total = self.db.execute(count_stmt).scalar_one()
        stmt = stmt.order_by(Booking.check_in_date.desc()).offset((page - 1) * page_size).limit(page_size)
        items = list(self.db.execute(stmt).unique().scalars().all())
        return items, total

    def search(
        self,
        page: int,
        page_size: int,
        status_filter: str | None = None,
        room_id: int | None = None,
        customer_id: int | None = None,
        check_in_from: date | None = None,
        check_in_to: date | None = None,
    ) -> tuple[list[Booking], int]:
        stmt = self._with_relations(select(Booking))
        count_stmt = select(func.count()).select_from(Booking)

        conditions = []
        if status_filter:
            conditions.append(Booking.status == status_filter)
        if room_id:
            conditions.append(Booking.room_id == room_id)
        if customer_id:
            conditions.append(Booking.customer_id == customer_id)
        if check_in_from:
            conditions.append(Booking.check_in_date >= check_in_from)
        if check_in_to:
            conditions.append(Booking.check_in_date <= check_in_to)

        for condition in conditions:
            stmt = stmt.where(condition)
            count_stmt = count_stmt.where(condition)

        total = self.db.execute(count_stmt).scalar_one()
        stmt = stmt.order_by(Booking.check_in_date.desc()).offset((page - 1) * page_size).limit(page_size)
        items = list(self.db.execute(stmt).unique().scalars().all())
        return items, total
