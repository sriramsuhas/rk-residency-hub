"""Direct database access for writing and reading audit log entries."""
from datetime import date, datetime, time, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from models.audit_log import AuditLog


class AuditLogRepository:
    def __init__(self, db: Session):
        self.db = db

    def log(
        self,
        action: str,
        user_id: int | None = None,
        entity_type: str | None = None,
        entity_id: int | None = None,
        details: str | None = None,
    ) -> AuditLog:
        entry = AuditLog(
            user_id=user_id, action=action, entity_type=entity_type, entity_id=entity_id, details=details
        )
        self.db.add(entry)
        self.db.commit()
        return entry

    def search(
        self,
        page: int,
        page_size: int,
        action: str | None = None,
        entity_type: str | None = None,
        user_id: int | None = None,
        date_from: date | None = None,
        date_to: date | None = None,
    ) -> tuple[list[AuditLog], int]:
        stmt = select(AuditLog).options(joinedload(AuditLog.user))
        count_stmt = select(func.count()).select_from(AuditLog)

        conditions = []
        if action:
            conditions.append(AuditLog.action == action)
        if entity_type:
            conditions.append(AuditLog.entity_type == entity_type)
        if user_id:
            conditions.append(AuditLog.user_id == user_id)
        if date_from:
            conditions.append(AuditLog.created_at >= datetime.combine(date_from, time.min, tzinfo=timezone.utc))
        if date_to:
            conditions.append(AuditLog.created_at <= datetime.combine(date_to, time.max, tzinfo=timezone.utc))

        for condition in conditions:
            stmt = stmt.where(condition)
            count_stmt = count_stmt.where(condition)

        total = self.db.execute(count_stmt).scalar_one()
        stmt = stmt.order_by(AuditLog.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
        items = list(self.db.execute(stmt).unique().scalars().all())
        return items, total
