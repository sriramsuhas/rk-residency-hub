"""
Direct database access for analytics dashboards. Every method here is a
read-only aggregation over data produced by earlier modules — no writes,
no business rules, just queries.
"""
from datetime import date, datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from models.booking import Booking
from models.enums import (
    AvailabilityStatus,
    BookingStatus,
    CleaningStatus,
    MaintenanceRequestStatus,
    PaymentStatus,
    RoleName,
)
from models.floor import Floor
from models.maintenance_request import MaintenanceRequest
from models.payment import Payment
from models.role import Role
from models.room import Room
from models.user import User


class AnalyticsRepository:
    def __init__(self, db: Session):
        self.db = db

    # --- Owner ---

    def total_revenue(self) -> float:
        stmt = select(func.coalesce(func.sum(Payment.amount), 0)).where(
            Payment.status == PaymentStatus.SUCCESS.value
        )
        return float(self.db.execute(stmt).scalar_one())

    def daily_revenue_trend(self, days: int = 30) -> list[tuple[date, float]]:
        since = datetime.now(timezone.utc) - timedelta(days=days)
        stmt = (
            select(func.date(Payment.paid_at), func.sum(Payment.amount))
            .where(Payment.status == PaymentStatus.SUCCESS.value, Payment.paid_at >= since)
            .group_by(func.date(Payment.paid_at))
            .order_by(func.date(Payment.paid_at))
        )
        return [(row[0], float(row[1])) for row in self.db.execute(stmt).all()]

    def occupancy_snapshot(self) -> tuple[int, int]:
        """Returns (active_room_count, occupied_room_count) as a current snapshot."""
        active_stmt = select(func.count()).select_from(Room).where(Room.is_active.is_(True))
        occupied_stmt = select(func.count()).select_from(Room).where(
            Room.is_active.is_(True), Room.availability_status == AvailabilityStatus.BOOKED.value
        )
        active = self.db.execute(active_stmt).scalar_one()
        occupied = self.db.execute(occupied_stmt).scalar_one()
        return active, occupied

    def booking_trend(self, days: int = 30) -> list[tuple[date, int]]:
        since = datetime.now(timezone.utc) - timedelta(days=days)
        stmt = (
            select(func.date(Booking.created_at), func.count())
            .where(Booking.created_at >= since)
            .group_by(func.date(Booking.created_at))
            .order_by(func.date(Booking.created_at))
        )
        return list(self.db.execute(stmt).all())

    def popular_rooms(self, limit: int = 5) -> list[tuple[int, str, int]]:
        stmt = (
            select(Room.id, Room.room_number, func.count(Booking.id))
            .join(Booking, Booking.room_id == Room.id)
            .where(Booking.status != BookingStatus.CANCELLED.value)
            .group_by(Room.id, Room.room_number)
            .order_by(func.count(Booking.id).desc())
            .limit(limit)
        )
        return list(self.db.execute(stmt).all())

    def customer_growth(self, days: int = 30) -> list[tuple[date, int]]:
        since = datetime.now(timezone.utc) - timedelta(days=days)
        stmt = (
            select(func.date(User.created_at), func.count())
            .join(Role, User.role_id == Role.id)
            .where(Role.name == RoleName.CUSTOMER.value, User.created_at >= since)
            .group_by(func.date(User.created_at))
            .order_by(func.date(User.created_at))
        )
        return list(self.db.execute(stmt).all())

    # --- Reception ---

    def todays_expected_checkins(self, today: date) -> int:
        stmt = (
            select(func.count())
            .select_from(Booking)
            .where(
                Booking.check_in_date == today,
                Booking.status.in_([BookingStatus.CONFIRMED.value, BookingStatus.CHECKED_IN.value]),
            )
        )
        return self.db.execute(stmt).scalar_one()

    def todays_expected_checkouts(self, today: date) -> int:
        stmt = (
            select(func.count())
            .select_from(Booking)
            .where(
                Booking.check_out_date == today,
                Booking.status.in_([BookingStatus.CHECKED_IN.value, BookingStatus.CHECKED_OUT.value]),
            )
        )
        return self.db.execute(stmt).scalar_one()

    def todays_revenue(self, today: date) -> float:
        stmt = select(func.coalesce(func.sum(Payment.amount), 0)).where(
            Payment.status == PaymentStatus.SUCCESS.value, func.date(Payment.paid_at) == today
        )
        return float(self.db.execute(stmt).scalar_one())

    def pending_bookings_count(self) -> int:
        stmt = select(func.count()).select_from(Booking).where(
            Booking.status == BookingStatus.PENDING_PAYMENT.value
        )
        return self.db.execute(stmt).scalar_one()

    # --- Housekeeping ---

    def pending_cleaning_rooms(self) -> list[Room]:
        stmt = (
            select(Room)
            .where(
                Room.is_active.is_(True),
                Room.cleaning_status.in_([CleaningStatus.DIRTY.value, CleaningStatus.IN_PROGRESS.value]),
            )
            .join(Floor, Room.floor_id == Floor.id)
            .order_by(Floor.floor_number, Room.room_number)
        )
        return list(self.db.execute(stmt).scalars().all())

    def pending_maintenance_count(self) -> int:
        active_statuses = [
            MaintenanceRequestStatus.PENDING.value,
            MaintenanceRequestStatus.ASSIGNED.value,
            MaintenanceRequestStatus.IN_PROGRESS.value,
        ]
        stmt = select(func.count()).select_from(MaintenanceRequest).where(
            MaintenanceRequest.status.in_(active_statuses)
        )
        return self.db.execute(stmt).scalar_one()

    def completed_today_count(self, today: date) -> int:
        stmt = select(func.count()).select_from(MaintenanceRequest).where(
            MaintenanceRequest.status == MaintenanceRequestStatus.COMPLETED.value,
            func.date(MaintenanceRequest.completed_at) == today,
        )
        return self.db.execute(stmt).scalar_one()
