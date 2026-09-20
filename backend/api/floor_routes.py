"""HTTP routes for floors. Read is public, writes are OWNER-only."""
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from auth.dependencies import require_roles
from database.session import get_db
from models.enums import RoleName
from models.user import User
from schemas.catalog_schemas import FloorCreateRequest, FloorResponse, FloorUpdateRequest
from services.catalog_service import FloorService
from utils.responses import success

router = APIRouter(prefix="/api/v1/floors", tags=["Floors"])


@router.get("", response_model=dict)
def list_floors(db: Session = Depends(get_db)):
    floors = FloorService(db).list_floors()
    return success([FloorResponse.model_validate(f).model_dump() for f in floors])


@router.post("", response_model=dict, status_code=status.HTTP_201_CREATED)
def create_floor(
    payload: FloorCreateRequest,
    db: Session = Depends(get_db),
    _owner: User = Depends(require_roles(RoleName.OWNER)),
):
    floor = FloorService(db).create_floor(payload)
    return success(FloorResponse.model_validate(floor).model_dump(), "Floor created")


@router.put("/{floor_id}", response_model=dict)
def update_floor(
    floor_id: int,
    payload: FloorUpdateRequest,
    db: Session = Depends(get_db),
    _owner: User = Depends(require_roles(RoleName.OWNER)),
):
    floor = FloorService(db).update_floor(floor_id, payload)
    return success(FloorResponse.model_validate(floor).model_dump(), "Floor updated")


@router.delete("/{floor_id}", response_model=dict)
def delete_floor(
    floor_id: int,
    db: Session = Depends(get_db),
    _owner: User = Depends(require_roles(RoleName.OWNER)),
):
    FloorService(db).delete_floor(floor_id)
    return success(None, "Floor deleted")
