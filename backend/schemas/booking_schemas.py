"""Request/response models for the booking engine."""
from datetime import date, datetime

from pydantic import BaseModel, Field, field_validator

from models.enums import BookingStatus
from schemas.room_schemas import RoomSummaryResponse
from schemas.user_schemas import UserResponse


class AvailabilityResponse(BaseModel):
    available: bool
    reason: str | None = None


class BookingCreateRequest(BaseModel):
    room_id: int
    check_in_date: date
    check_out_date: date
    num_guests: int = Field(gt=0)
    special_requests: str | None = Field(default=None, max_length=500)

    @field_validator("check_out_date")
    @classmethod
    def check_out_after_check_in(cls, v, info):
        check_in = info.data.get("check_in_date")
        if check_in is not None and v <= check_in:
            raise ValueError("check_out_date must be after check_in_date")
        return v


class BookingCancelRequest(BaseModel):
    reason: str | None = Field(default=None, max_length=255)


class AssignRoomRequest(BaseModel):
    room_id: int


class BookingResponse(BaseModel):
    id: int
    check_in_date: date
    check_out_date: date
    num_guests: int
    status: BookingStatus
    total_amount: float
    special_requests: str | None
    cancelled_at: datetime | None
    cancellation_reason: str | None
    checked_in_at: datetime | None
    checked_out_at: datetime | None
    created_at: datetime
    room: RoomSummaryResponse
    customer: UserResponse

    model_config = {"from_attributes": True}


class PaginatedBookings(BaseModel):
    total: int
    page: int
    page_size: int
    items: list[BookingResponse]
