"""Request/response models for rooms, including search/filter params and image metadata."""
from datetime import datetime

from pydantic import BaseModel, Field

from models.enums import AvailabilityStatus, CleaningStatus, RoomMaintenanceFlag
from schemas.catalog_schemas import AmenityResponse, FloorResponse, RoomTypeResponse


class RoomImageResponse(BaseModel):
    id: int
    image_url: str
    is_primary: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class RoomCreateRequest(BaseModel):
    room_number: str = Field(min_length=1, max_length=10)
    floor_id: int
    room_type_id: int
    price_per_night: float = Field(gt=0)
    capacity: int = Field(gt=0)
    description: str | None = Field(default=None, max_length=1000)
    amenity_ids: list[int] = Field(default_factory=list)


class RoomUpdateRequest(BaseModel):
    room_number: str | None = Field(default=None, min_length=1, max_length=10)
    floor_id: int | None = None
    room_type_id: int | None = None
    price_per_night: float | None = Field(default=None, gt=0)
    capacity: int | None = Field(default=None, gt=0)
    description: str | None = Field(default=None, max_length=1000)


class AmenityAssignmentRequest(BaseModel):
    amenity_ids: list[int]


class AvailabilityUpdateRequest(BaseModel):
    availability_status: AvailabilityStatus


class CleaningStatusUpdateRequest(BaseModel):
    cleaning_status: CleaningStatus


class RoomSummaryResponse(BaseModel):
    """Lighter-weight shape used in search/listing results."""

    id: int
    room_number: str
    price_per_night: float
    capacity: int
    availability_status: AvailabilityStatus
    room_type: RoomTypeResponse
    floor: FloorResponse
    primary_image_url: str | None = None

    model_config = {"from_attributes": True}


class RoomDetailResponse(BaseModel):
    id: int
    room_number: str
    price_per_night: float
    capacity: int
    description: str | None
    availability_status: AvailabilityStatus
    cleaning_status: CleaningStatus
    maintenance_status: RoomMaintenanceFlag
    is_active: bool
    floor: FloorResponse
    room_type: RoomTypeResponse
    amenities: list[AmenityResponse]
    images: list[RoomImageResponse]

    model_config = {"from_attributes": True}


class PaginatedRooms(BaseModel):
    total: int
    page: int
    page_size: int
    items: list[RoomSummaryResponse]
