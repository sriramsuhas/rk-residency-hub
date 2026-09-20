"""Request/response models for floors, room types, and amenities — the lookup tables rooms reference."""
from pydantic import BaseModel, Field


class FloorCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=50)
    floor_number: int
    description: str | None = Field(default=None, max_length=255)


class FloorUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=50)
    floor_number: int | None = None
    description: str | None = Field(default=None, max_length=255)


class FloorResponse(BaseModel):
    id: int
    name: str
    floor_number: int
    description: str | None

    model_config = {"from_attributes": True}


class RoomTypeCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=60)
    description: str | None = Field(default=None, max_length=500)
    base_price: float = Field(gt=0)
    max_occupancy: int = Field(gt=0)


class RoomTypeUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=60)
    description: str | None = Field(default=None, max_length=500)
    base_price: float | None = Field(default=None, gt=0)
    max_occupancy: int | None = Field(default=None, gt=0)


class RoomTypeResponse(BaseModel):
    id: int
    name: str
    description: str | None
    base_price: float
    max_occupancy: int

    model_config = {"from_attributes": True}


class AmenityCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=60)
    icon: str | None = Field(default=None, max_length=50)


class AmenityResponse(BaseModel):
    id: int
    name: str
    icon: str | None

    model_config = {"from_attributes": True}
