"""HTTP routes for the three role dashboards."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from auth.dependencies import require_roles
from database.session import get_db
from models.enums import RoleName
from models.user import User
from schemas.analytics_schemas import (
    HousekeepingAnalyticsResponse,
    OwnerAnalyticsResponse,
    ReceptionAnalyticsResponse,
)
from services.analytics_service import AnalyticsService
from utils.responses import success

router = APIRouter(prefix="/api/v1/analytics", tags=["Analytics"])


@router.get("/owner", response_model=dict)
def owner_dashboard(
    db: Session = Depends(get_db),
    _owner: User = Depends(require_roles(RoleName.OWNER)),
):
    data = AnalyticsService(db).owner_dashboard()
    return success(OwnerAnalyticsResponse.model_validate(data).model_dump())


@router.get("/reception", response_model=dict)
def reception_dashboard(
    db: Session = Depends(get_db),
    _staff: User = Depends(require_roles(RoleName.RECEPTION, RoleName.OWNER)),
):
    data = AnalyticsService(db).reception_dashboard()
    return success(ReceptionAnalyticsResponse.model_validate(data).model_dump())


@router.get("/housekeeping", response_model=dict)
def housekeeping_dashboard(
    db: Session = Depends(get_db),
    _staff: User = Depends(require_roles(RoleName.HOUSEKEEPING, RoleName.OWNER)),
):
    data = AnalyticsService(db).housekeeping_dashboard()
    return success(HousekeepingAnalyticsResponse.model_validate(data).model_dump())
