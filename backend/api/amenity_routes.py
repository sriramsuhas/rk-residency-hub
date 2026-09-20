"""HTTP routes for amenities. Read is public, writes are OWNER-only."""
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from auth.dependencies import require_roles
from database.session import get_db
from models.enums import RoleName
from models.user import User
from schemas.catalog_schemas import AmenityCreateRequest, AmenityResponse
from services.catalog_service import AmenityService
from utils.responses import success

router = APIRouter(prefix="/api/v1/amenities", tags=["Amenities"])


@router.get("", response_model=dict)
def list_amenities(db: Session = Depends(get_db)):
    amenities = AmenityService(db).list_amenities()
    return success([AmenityResponse.model_validate(a).model_dump() for a in amenities])


@router.post("", response_model=dict, status_code=status.HTTP_201_CREATED)
def create_amenity(
    payload: AmenityCreateRequest,
    db: Session = Depends(get_db),
    _owner: User = Depends(require_roles(RoleName.OWNER)),
):
    amenity = AmenityService(db).create_amenity(payload)
    return success(AmenityResponse.model_validate(amenity).model_dump(), "Amenity created")


@router.delete("/{amenity_id}", response_model=dict)
def delete_amenity(
    amenity_id: int,
    db: Session = Depends(get_db),
    _owner: User = Depends(require_roles(RoleName.OWNER)),
):
    AmenityService(db).delete_amenity(amenity_id)
    return success(None, "Amenity deleted")
