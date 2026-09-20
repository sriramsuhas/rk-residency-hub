"""Business logic for the three role dashboards. Thin — mostly composes repository aggregations."""
from datetime import date, timezone, datetime

from sqlalchemy.orm import Session

from repositories.analytics_repository import AnalyticsRepository
from services.maintenance_service import MaintenanceService


class AnalyticsService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = AnalyticsRepository(db)
        self.maintenance_service = MaintenanceService(db)

    def owner_dashboard(self) -> dict:
        active_rooms, occupied_rooms = self.repo.occupancy_snapshot()
        occupancy_rate = round((occupied_rooms / active_rooms) * 100, 1) if active_rooms > 0 else 0.0

        revenue_trend = self.repo.daily_revenue_trend(days=30)
        booking_trend = self.repo.booking_trend(days=30)
        customer_growth = self.repo.customer_growth(days=30)
        popular_rooms = self.repo.popular_rooms(limit=5)

        return {
            "total_revenue": self.repo.total_revenue(),
            "revenue_last_30_days": sum(v for _, v in revenue_trend),
            "daily_revenue_trend": [{"date": d, "value": v} for d, v in revenue_trend],
            "occupancy_rate": occupancy_rate,
            "active_room_count": active_rooms,
            "occupied_room_count": occupied_rooms,
            "booking_trend": [{"date": d, "value": c} for d, c in booking_trend],
            "popular_rooms": [
                {"room_id": rid, "room_number": rnum, "booking_count": count}
                for rid, rnum, count in popular_rooms
            ],
            "customer_growth": [{"date": d, "value": c} for d, c in customer_growth],
            "maintenance_stats": self.maintenance_service.get_stats(),
        }

    def reception_dashboard(self) -> dict:
        today = datetime.now(timezone.utc).date()
        return {
            "todays_expected_checkins": self.repo.todays_expected_checkins(today),
            "todays_expected_checkouts": self.repo.todays_expected_checkouts(today),
            "todays_revenue": self.repo.todays_revenue(today),
            "pending_bookings_count": self.repo.pending_bookings_count(),
        }

    def housekeeping_dashboard(self) -> dict:
        today = datetime.now(timezone.utc).date()
        rooms = self.repo.pending_cleaning_rooms()
        return {
            "pending_cleaning_count": len(rooms),
            "pending_cleaning_rooms": [
                {
                    "room_id": r.id,
                    "room_number": r.room_number,
                    "floor_name": r.floor.name,
                    "cleaning_status": r.cleaning_status,
                }
                for r in rooms
            ],
            "pending_maintenance_count": self.repo.pending_maintenance_count(),
            "completed_today_count": self.repo.completed_today_count(today),
        }
