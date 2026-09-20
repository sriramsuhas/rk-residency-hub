"""Direct database access for report generation. Read-only, no business rules."""
from datetime import date, datetime, time, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from models.booking import Booking
from models.enums import BookingStatus, PaymentStatus, RoleName
from models.maintenance_request import MaintenanceRequest
from models.payment import Payment
from models.role import Role
from models.room import Room
from models.user import User


def _day_bounds(d: date) -> tuple[datetime, datetime]:
    start = datetime.combine(d, time.min, tzinfo=timezone.utc)
    end = datetime.combine(d, time.max, tzinfo=timezone.utc)
    return start, end


class ReportRepository:
    def __init__(self, db: Session):
        self.db = db

    def payments_in_range(self, date_from: date, date_to: date) -> list[Payment]:
        start, end = _day_bounds(date_from)[0], _day_bounds(date_to)[1]
        stmt = (
            select(Payment)
            .options(
                joinedload(Payment.booking).joinedload(Booking.room),
                joinedload(Payment.booking).joinedload(Booking.customer),
            )
            .where(Payment.paid_at >= start, Payment.paid_at <= end)
            .order_by(Payment.paid_at)
        )
        return list(self.db.execute(stmt).unique().scalars().all())

    def bookings_in_range(self, date_from: date, date_to: date, status_filter: str | None) -> list[Booking]:
        start, end = _day_bounds(date_from)[0], _day_bounds(date_to)[1]
        stmt = (
            select(Booking)
            .options(joinedload(Booking.room), joinedload(Booking.customer))
            .where(Booking.created_at >= start, Booking.created_at <= end)
        )
        if status_filter:
            stmt = stmt.where(Booking.status == status_filter)
        stmt = stmt.order_by(Booking.created_at)
        return list(self.db.execute(stmt).unique().scalars().all())

    def maintenance_in_range(
        self, date_from: date, date_to: date, status_filter: str | None
    ) -> list[MaintenanceRequest]:
        start, end = _day_bounds(date_from)[0], _day_bounds(date_to)[1]
        stmt = (
            select(MaintenanceRequest)
            .options(joinedload(MaintenanceRequest.room), joinedload(MaintenanceRequest.assigned_staff))
            .where(MaintenanceRequest.created_at >= start, MaintenanceRequest.created_at <= end)
        )
        if status_filter:
            stmt = stmt.where(MaintenanceRequest.status == status_filter)
        stmt = stmt.order_by(MaintenanceRequest.created_at)
        return list(self.db.execute(stmt).unique().scalars().all())

    def occupancy_by_day(self, date_from: date, date_to: date) -> list[tuple[date, int, int]]:
        """Returns (day, occupied_room_count, active_room_count) for each day in range."""
        active_room_count = self.db.execute(
            select(func.count()).select_from(Room).where(Room.is_active.is_(True))
        ).scalar_one()

        active_statuses = [
            BookingStatus.CONFIRMED.value,
            BookingStatus.CHECKED_IN.value,
            BookingStatus.CHECKED_OUT.value,
        ]

        results = []
        current = date_from
        # Capped so a wide date range can't turn this into an unbounded loop of queries.
        max_days = 92
        day_count = 0
        while current <= date_to and day_count < max_days:
            stmt = select(func.count(func.distinct(Booking.room_id))).where(
                Booking.check_in_date <= current,
                Booking.check_out_date > current,
                Booking.status.in_(active_statuses),
            )
            occupied = self.db.execute(stmt).scalar_one()
            results.append((current, occupied, active_room_count))
            current += timedelta(days=1)
            day_count += 1
        return results

    def customer_summary(self) -> list[tuple[User, int, float]]:
        """Returns (user, total_bookings, total_spent) for every CUSTOMER."""
        customers_stmt = (
            select(User)
            .join(Role, User.role_id == Role.id)
            .where(Role.name == RoleName.CUSTOMER.value)
            .order_by(User.created_at)
        )
        customers = list(self.db.execute(customers_stmt).scalars().all())

        booking_counts_stmt = (
            select(Booking.customer_id, func.count())
            .where(Booking.status != BookingStatus.CANCELLED.value)
            .group_by(Booking.customer_id)
        )
        booking_counts = dict(self.db.execute(booking_counts_stmt).all())

        spend_stmt = (
            select(Booking.customer_id, func.coalesce(func.sum(Payment.amount), 0))
            .join(Payment, Payment.booking_id == Booking.id)
            .where(Payment.status == PaymentStatus.SUCCESS.value)
            .group_by(Booking.customer_id)
        )
        spend = {cid: float(total) for cid, total in self.db.execute(spend_stmt).all()}

        return [(c, booking_counts.get(c.id, 0), spend.get(c.id, 0.0)) for c in customers]
