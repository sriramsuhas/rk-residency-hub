"""
In-app notification service. `notify()` is the integration point other
services call to push a notification to a user — no email/push, just an
in-app inbox.
"""
from sqlalchemy.orm import Session

from models.enums import NotificationType
from models.notification import Notification
from repositories.notification_repository import NotificationRepository
from utils.exceptions import NotFoundError, UnauthorizedError


class NotificationService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = NotificationRepository(db)

    def notify(
        self,
        user_id: int,
        title: str,
        message: str,
        notification_type: NotificationType,
        related_entity_type: str | None = None,
        related_entity_id: int | None = None,
    ) -> Notification:
        notification = Notification(
            user_id=user_id,
            title=title,
            message=message,
            type=notification_type,
            related_entity_type=related_entity_type,
            related_entity_id=related_entity_id,
        )
        return self.repo.create(notification)

    def list_for_user(self, user_id: int, page: int, page_size: int):
        return self.repo.list_for_user(user_id, page, page_size)

    def mark_read(self, notification_id: int, requester_id: int) -> Notification:
        notification = self.repo.get_by_id(notification_id)
        if notification is None:
            raise NotFoundError("Notification not found")
        if notification.user_id != requester_id:
            raise UnauthorizedError("You do not have access to this notification")
        notification.is_read = True
        return self.repo.update(notification)

    def mark_all_read(self, user_id: int) -> None:
        self.repo.mark_all_read(user_id)
