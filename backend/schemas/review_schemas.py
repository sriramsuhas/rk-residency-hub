"""Request/response models for reviews."""
from datetime import datetime

from pydantic import BaseModel, Field

from schemas.user_schemas import UserResponse


class ReviewCreateRequest(BaseModel):
    booking_id: int
    rating: int = Field(ge=1, le=5)
    comment: str | None = Field(default=None, max_length=1000)


class ReviewUpdateRequest(BaseModel):
    rating: int | None = Field(default=None, ge=1, le=5)
    comment: str | None = Field(default=None, max_length=1000)


class ReviewResponse(BaseModel):
    id: int
    room_id: int
    booking_id: int
    rating: int
    comment: str | None
    created_at: datetime
    customer: UserResponse

    model_config = {"from_attributes": True}


class PaginatedReviews(BaseModel):
    total: int
    page: int
    page_size: int
    average_rating: float | None
    items: list[ReviewResponse]
