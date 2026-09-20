"""HTTP routes for in-app notifications."""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from auth.dependencies import get_current_user
from database.session import get_db
from models.user import User
from schemas.notification_schemas import NotificationResponse, PaginatedNotifications
from services.notification_service import NotificationService
from utils.responses import success

router = APIRouter(prefix="/api/v1/notifications", tags=["Notifications"])


@router.get("", response_model=dict)
def list_notifications(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=50),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    items, total, unread_count = NotificationService(db).list_for_user(current_user.id, page, page_size)
    body = PaginatedNotifications(
        total=total, unread_count=unread_count, page=page, page_size=page_size,
        items=[NotificationResponse.model_validate(n) for n in items],
    )
    return success(body.model_dump())


@router.patch("/read-all", response_model=dict)
def mark_all_read(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    NotificationService(db).mark_all_read(current_user.id)
    return success(None, "All notifications marked as read")


@router.patch("/{notification_id}/read", response_model=dict)
def mark_read(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    notification = NotificationService(db).mark_read(notification_id, current_user.id)
    return success(NotificationResponse.model_validate(notification).model_dump(), "Marked as read")
