"""HTTP routes for user profile self-service and OWNER-only user administration."""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from auth.dependencies import get_current_user, require_roles
from database.session import get_db
from models.enums import RoleName
from models.user import User
from schemas.user_schemas import (
    PaginatedUsers,
    UpdateProfileRequest,
    UpdateRoleRequest,
    UpdateStatusRequest,
    UserResponse,
)
from services.user_service import UserService
from utils.responses import success

router = APIRouter(prefix="/api/v1/users", tags=["Users"])


@router.get("/me", response_model=dict)
def get_my_profile(current_user: User = Depends(get_current_user)):
    return success(UserResponse.model_validate(current_user).model_dump())


@router.put("/me", response_model=dict)
def update_my_profile(
    payload: UpdateProfileRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    updated = UserService(db).update_profile(current_user, payload)
    return success(UserResponse.model_validate(updated).model_dump(), "Profile updated")


@router.get("", response_model=dict)
def list_users(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    search: str | None = None,
    role: str | None = None,
    db: Session = Depends(get_db),
    _staff: User = Depends(require_roles(RoleName.OWNER, RoleName.RECEPTION)),
):
    items, total = UserService(db).list_users(page, page_size, search, role)
    body = PaginatedUsers(
        total=total,
        page=page,
        page_size=page_size,
        items=[UserResponse.model_validate(u) for u in items],
    )
    return success(body.model_dump())


@router.patch("/{user_id}/role", response_model=dict)
def change_user_role(
    user_id: int,
    payload: UpdateRoleRequest,
    db: Session = Depends(get_db),
    owner: User = Depends(require_roles(RoleName.OWNER)),
):
    updated = UserService(db).change_role(user_id, payload.role.value, owner)
    return success(UserResponse.model_validate(updated).model_dump(), "Role updated")


@router.patch("/{user_id}/status", response_model=dict)
def change_user_status(
    user_id: int,
    payload: UpdateStatusRequest,
    db: Session = Depends(get_db),
    owner: User = Depends(require_roles(RoleName.OWNER)),
):
    updated = UserService(db).change_status(user_id, payload.is_active, owner)
    return success(UserResponse.model_validate(updated).model_dump(), "Status updated")
