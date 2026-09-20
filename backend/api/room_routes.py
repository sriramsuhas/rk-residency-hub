"""
HTTP routes for rooms.

Browsing (search, detail) is public so guests can shop rooms before logging
in. Everything that mutates state is role-gated.
"""
from datetime import date

from fastapi import APIRouter, Depends, File, Query, UploadFile, status
from sqlalchemy.orm import Session

from auth.dependencies import get_current_user, require_roles
from database.session import get_db
from models.enums import RoleName
from models.room import Room
from models.user import User
from schemas.booking_schemas import AvailabilityResponse
from schemas.review_schemas import PaginatedReviews, ReviewResponse
from schemas.room_schemas import (
    AmenityAssignmentRequest,
    AvailabilityUpdateRequest,
    CleaningStatusUpdateRequest,
    PaginatedRooms,
    RoomCreateRequest,
    RoomDetailResponse,
    RoomSummaryResponse,
    RoomUpdateRequest,
)
from services.booking_service import BookingService
from services.review_service import ReviewService
from services.room_service import RoomService
from utils.responses import success

router = APIRouter(prefix="/api/v1/rooms", tags=["Rooms"])


def _to_summary(room: Room) -> dict:
    """Builds the lightweight listing shape, including the derived primary image."""
    primary = next((img for img in room.images if img.is_primary), None)
    if primary is None and room.images:
        primary = room.images[0]
    data = RoomSummaryResponse.model_validate(room).model_dump()
    data["primary_image_url"] = primary.image_url if primary else None
    return data


@router.get("", response_model=dict)
def search_rooms(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    search: str | None = None,
    floor_id: int | None = None,
    room_type_id: int | None = None,
    min_price: float | None = Query(default=None, ge=0),
    max_price: float | None = Query(default=None, ge=0),
    capacity: int | None = Query(default=None, ge=1),
    availability_status: str | None = None,
    amenity_ids: list[int] | None = Query(default=None),
    sort_by: str = Query(default="room_number", pattern="^(price_asc|price_desc|room_number)$"),
    db: Session = Depends(get_db),
):
    items, total = RoomService(db).search_rooms(
        page=page,
        page_size=page_size,
        search=search,
        floor_id=floor_id,
        room_type_id=room_type_id,
        min_price=min_price,
        max_price=max_price,
        capacity=capacity,
        availability_status=availability_status,
        amenity_ids=amenity_ids,
        sort_by=sort_by,
    )
    body = PaginatedRooms(
        total=total, page=page, page_size=page_size, items=[_to_summary(r) for r in items]
    )
    return success(body.model_dump())


@router.get("/{room_id}", response_model=dict)
def get_room(room_id: int, db: Session = Depends(get_db)):
    room = RoomService(db).get_room(room_id)
    return success(RoomDetailResponse.model_validate(room).model_dump())


@router.get("/{room_id}/availability", response_model=dict)
def check_room_availability(
    room_id: int,
    check_in: date = Query(...),
    check_out: date = Query(...),
    db: Session = Depends(get_db),
):
    available, reason = BookingService(db).check_availability(room_id, check_in, check_out)
    return success(AvailabilityResponse(available=available, reason=reason).model_dump())


@router.post("", response_model=dict, status_code=status.HTTP_201_CREATED)
def create_room(
    payload: RoomCreateRequest,
    db: Session = Depends(get_db),
    owner: User = Depends(require_roles(RoleName.OWNER)),
):
    room = RoomService(db).create_room(payload, owner.id)
    return success(RoomDetailResponse.model_validate(room).model_dump(), "Room created")


@router.put("/{room_id}", response_model=dict)
def update_room(
    room_id: int,
    payload: RoomUpdateRequest,
    db: Session = Depends(get_db),
    owner: User = Depends(require_roles(RoleName.OWNER)),
):
    room = RoomService(db).update_room(room_id, payload, owner.id)
    return success(RoomDetailResponse.model_validate(room).model_dump(), "Room updated")


@router.delete("/{room_id}", response_model=dict)
def deactivate_room(
    room_id: int,
    db: Session = Depends(get_db),
    owner: User = Depends(require_roles(RoleName.OWNER)),
):
    RoomService(db).deactivate_room(room_id, owner.id)
    return success(None, "Room deactivated")


@router.patch("/{room_id}/availability", response_model=dict)
def update_availability(
    room_id: int,
    payload: AvailabilityUpdateRequest,
    db: Session = Depends(get_db),
    actor: User = Depends(require_roles(RoleName.RECEPTION, RoleName.OWNER)),
):
    room = RoomService(db).update_availability(room_id, payload.availability_status.value, actor.id)
    return success(RoomDetailResponse.model_validate(room).model_dump(), "Availability updated")


@router.patch("/{room_id}/cleaning-status", response_model=dict)
def update_cleaning_status(
    room_id: int,
    payload: CleaningStatusUpdateRequest,
    db: Session = Depends(get_db),
    actor: User = Depends(require_roles(RoleName.HOUSEKEEPING, RoleName.RECEPTION, RoleName.OWNER)),
):
    room = RoomService(db).update_cleaning_status(room_id, payload.cleaning_status.value, actor.id)
    return success(RoomDetailResponse.model_validate(room).model_dump(), "Cleaning status updated")


@router.patch("/{room_id}/amenities", response_model=dict)
def set_amenities(
    room_id: int,
    payload: AmenityAssignmentRequest,
    db: Session = Depends(get_db),
    owner: User = Depends(require_roles(RoleName.OWNER)),
):
    room = RoomService(db).set_amenities(room_id, payload.amenity_ids, owner.id)
    return success(RoomDetailResponse.model_validate(room).model_dump(), "Amenities updated")


@router.post("/{room_id}/images", response_model=dict)
def upload_room_image(
    room_id: int,
    file: UploadFile = File(...),
    is_primary: bool = Query(default=False),
    db: Session = Depends(get_db),
    owner: User = Depends(require_roles(RoleName.OWNER)),
):
    room = RoomService(db).add_image(room_id, file, is_primary, owner.id)
    return success(RoomDetailResponse.model_validate(room).model_dump(), "Image uploaded")


@router.delete("/{room_id}/images/{image_id}", response_model=dict)
def delete_room_image(
    room_id: int,
    image_id: int,
    db: Session = Depends(get_db),
    owner: User = Depends(require_roles(RoleName.OWNER)),
):
    room = RoomService(db).delete_image(room_id, image_id, owner.id)
    return success(RoomDetailResponse.model_validate(room).model_dump(), "Image deleted")


@router.get("/{room_id}/reviews", response_model=dict)
def list_room_reviews(
    room_id: int,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=50),
    db: Session = Depends(get_db),
):
    items, total, average_rating = ReviewService(db).list_for_room(room_id, page, page_size)
    body = PaginatedReviews(
        total=total, page=page, page_size=page_size, average_rating=average_rating,
        items=[ReviewResponse.model_validate(r) for r in items],
    )
    return success(body.model_dump())
