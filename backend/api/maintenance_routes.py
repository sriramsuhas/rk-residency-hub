"""HTTP routes for the maintenance workflow."""
from fastapi import APIRouter, Depends, File, Form, Query, UploadFile, status
from sqlalchemy.orm import Session

from auth.dependencies import get_current_user, require_roles
from database.session import get_db
from models.enums import MaintenanceCategory, MaintenancePriority, RoleName
from models.user import User
from schemas.maintenance_schemas import (
    MaintenanceAssignRequest,
    MaintenanceCancelRequest,
    MaintenanceRequestResponse,
    MaintenanceStatsResponse,
    PaginatedMaintenanceRequests,
)
from services.maintenance_service import MaintenanceService
from utils.responses import success

router = APIRouter(prefix="/api/v1/maintenance-requests", tags=["Maintenance"])


@router.post("", response_model=dict, status_code=status.HTTP_201_CREATED)
def create_request(
    room_id: int = Form(...),
    category: MaintenanceCategory = Form(...),
    priority: MaintenancePriority = Form(default=MaintenancePriority.MEDIUM),
    description: str = Form(..., min_length=5, max_length=1000),
    booking_id: int | None = Form(default=None),
    image: UploadFile | None = File(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(RoleName.CUSTOMER)),
):
    from schemas.maintenance_schemas import MaintenanceRequestCreateRequest

    payload = MaintenanceRequestCreateRequest(
        room_id=room_id, booking_id=booking_id, category=category, priority=priority, description=description
    )
    request = MaintenanceService(db).create_request(payload, current_user.id, image)
    return success(MaintenanceRequestResponse.model_validate(request).model_dump(), "Request submitted")


@router.get("/me", response_model=dict)
def my_requests(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=50),
    status_filter: str | None = Query(default=None, alias="status"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(RoleName.CUSTOMER)),
):
    items, total = MaintenanceService(db).list_my_requests(current_user.id, page, page_size, status_filter)
    body = PaginatedMaintenanceRequests(
        total=total, page=page, page_size=page_size,
        items=[MaintenanceRequestResponse.model_validate(r) for r in items],
    )
    return success(body.model_dump())


@router.get("/my-tasks", response_model=dict)
def my_tasks(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=50),
    status_filter: str | None = Query(default=None, alias="status"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(RoleName.HOUSEKEEPING)),
):
    items, total = MaintenanceService(db).list_my_tasks(current_user.id, page, page_size, status_filter)
    body = PaginatedMaintenanceRequests(
        total=total, page=page, page_size=page_size,
        items=[MaintenanceRequestResponse.model_validate(r) for r in items],
    )
    return success(body.model_dump())


@router.get("/stats", response_model=dict)
def get_stats(
    db: Session = Depends(get_db),
    _staff: User = Depends(require_roles(RoleName.RECEPTION, RoleName.OWNER)),
):
    stats = MaintenanceService(db).get_stats()
    return success(MaintenanceStatsResponse.model_validate(stats).model_dump())


@router.get("", response_model=dict)
def search_requests(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    status_filter: str | None = Query(default=None, alias="status"),
    category: str | None = None,
    priority: str | None = None,
    room_id: int | None = None,
    assigned_staff_id: int | None = None,
    db: Session = Depends(get_db),
    _staff: User = Depends(require_roles(RoleName.RECEPTION, RoleName.OWNER)),
):
    items, total = MaintenanceService(db).search_requests(
        page=page, page_size=page_size, status_filter=status_filter, category=category,
        priority=priority, room_id=room_id, assigned_staff_id=assigned_staff_id,
    )
    body = PaginatedMaintenanceRequests(
        total=total, page=page, page_size=page_size,
        items=[MaintenanceRequestResponse.model_validate(r) for r in items],
    )
    return success(body.model_dump())


@router.get("/{request_id}", response_model=dict)
def get_request(
    request_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    request = MaintenanceService(db).get_request_for_viewer(request_id, current_user.id, current_user.role.name)
    return success(MaintenanceRequestResponse.model_validate(request).model_dump())


@router.patch("/{request_id}/assign", response_model=dict)
def assign_request(
    request_id: int,
    payload: MaintenanceAssignRequest,
    db: Session = Depends(get_db),
    actor: User = Depends(require_roles(RoleName.RECEPTION, RoleName.OWNER)),
):
    request = MaintenanceService(db).assign(request_id, payload.staff_id, payload.priority, actor.id)
    return success(MaintenanceRequestResponse.model_validate(request).model_dump(), "Request assigned")


@router.post("/{request_id}/start", response_model=dict)
def start_request(
    request_id: int,
    db: Session = Depends(get_db),
    actor: User = Depends(require_roles(RoleName.HOUSEKEEPING)),
):
    request = MaintenanceService(db).start(request_id, actor.id)
    return success(MaintenanceRequestResponse.model_validate(request).model_dump(), "Task started")


@router.post("/{request_id}/complete", response_model=dict)
def complete_request(
    request_id: int,
    remarks: str | None = Form(default=None, max_length=1000),
    image: UploadFile | None = File(default=None),
    db: Session = Depends(get_db),
    actor: User = Depends(require_roles(RoleName.HOUSEKEEPING)),
):
    request = MaintenanceService(db).complete(request_id, remarks, image, actor.id)
    return success(MaintenanceRequestResponse.model_validate(request).model_dump(), "Task completed")


@router.post("/{request_id}/cancel", response_model=dict)
def cancel_request(
    request_id: int,
    payload: MaintenanceCancelRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    request = MaintenanceService(db).cancel(request_id, current_user.id, current_user.role.name, payload.reason)
    return success(MaintenanceRequestResponse.model_validate(request).model_dump(), "Request cancelled")
