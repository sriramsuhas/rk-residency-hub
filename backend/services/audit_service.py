"""Business logic for reading the audit trail. Read-only — writing happens via AuditLogRepository.log() calls scattered through the other services."""
from datetime import date

from sqlalchemy.orm import Session

from repositories.audit_log_repository import AuditLogRepository


class AuditLogService:
    def __init__(self, db: Session):
        self.repo = AuditLogRepository(db)

    def search(
        self,
        page: int,
        page_size: int,
        action: str | None = None,
        entity_type: str | None = None,
        user_id: int | None = None,
        date_from: date | None = None,
        date_to: date | None = None,
    ):
        return self.repo.search(
            page=page,
            page_size=page_size,
            action=action,
            entity_type=entity_type,
            user_id=user_id,
            date_from=date_from,
            date_to=date_to,
        )
