"""Request/response models for in-app notifications."""
from datetime import datetime

from pydantic import BaseModel

from models.enums import NotificationType


class NotificationResponse(BaseModel):
    id: int
    title: str
    message: str
    type: NotificationType
    related_entity_type: str | None
    related_entity_id: int | None
    is_read: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class PaginatedNotifications(BaseModel):
    total: int
    unread_count: int
    page: int
    page_size: int
    items: list[NotificationResponse]
