"""HTTP routes for room types. Read is public, writes are OWNER-only."""
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from auth.dependencies import require_roles
from database.session import get_db
from models.enums import RoleName
from models.user import User
from schemas.catalog_schemas import RoomTypeCreateRequest, RoomTypeResponse, RoomTypeUpdateRequest
from services.catalog_service import RoomTypeService
from utils.responses import success

router = APIRouter(prefix="/api/v1/room-types", tags=["Room Types"])


@router.get("", response_model=dict)
def list_room_types(db: Session = Depends(get_db)):
    room_types = RoomTypeService(db).list_room_types()
    return success([RoomTypeResponse.model_validate(rt).model_dump() for rt in room_types])


@router.post("", response_model=dict, status_code=status.HTTP_201_CREATED)
def create_room_type(
    payload: RoomTypeCreateRequest,
    db: Session = Depends(get_db),
    _owner: User = Depends(require_roles(RoleName.OWNER)),
):
    room_type = RoomTypeService(db).create_room_type(payload)
    return success(RoomTypeResponse.model_validate(room_type).model_dump(), "Room type created")


@router.put("/{room_type_id}", response_model=dict)
def update_room_type(
    room_type_id: int,
    payload: RoomTypeUpdateRequest,
    db: Session = Depends(get_db),
    _owner: User = Depends(require_roles(RoleName.OWNER)),
):
    room_type = RoomTypeService(db).update_room_type(room_type_id, payload)
    return success(RoomTypeResponse.model_validate(room_type).model_dump(), "Room type updated")


@router.delete("/{room_type_id}", response_model=dict)
def delete_room_type(
    room_type_id: int,
    db: Session = Depends(get_db),
    _owner: User = Depends(require_roles(RoleName.OWNER)),
):
    RoomTypeService(db).delete_room_type(room_type_id)
    return success(None, "Room type deleted")
