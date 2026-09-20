"""Response models for the Owner, Reception, and Housekeeping analytics dashboards."""
from datetime import date

from pydantic import BaseModel

from schemas.maintenance_schemas import MaintenanceStatsResponse


class DailyPoint(BaseModel):
    date: date
    value: float


class PopularRoom(BaseModel):
    room_id: int
    room_number: str
    booking_count: int


class OwnerAnalyticsResponse(BaseModel):
    total_revenue: float
    revenue_last_30_days: float
    daily_revenue_trend: list[DailyPoint]
    occupancy_rate: float
    active_room_count: int
    occupied_room_count: int
    booking_trend: list[DailyPoint]
    popular_rooms: list[PopularRoom]
    customer_growth: list[DailyPoint]
    maintenance_stats: MaintenanceStatsResponse


class ReceptionAnalyticsResponse(BaseModel):
    todays_expected_checkins: int
    todays_expected_checkouts: int
    todays_revenue: float
    pending_bookings_count: int


class PendingCleaningRoom(BaseModel):
    room_id: int
    room_number: str
    floor_name: str
    cleaning_status: str


class HousekeepingAnalyticsResponse(BaseModel):
    pending_cleaning_count: int
    pending_cleaning_rooms: list[PendingCleaningRoom]
    pending_maintenance_count: int
    completed_today_count: int
