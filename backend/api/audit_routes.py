"""HTTP routes for the audit trail. OWNER-only — this is a security/compliance view."""
from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from auth.dependencies import require_roles
from database.session import get_db
from models.enums import RoleName
from models.user import User
from schemas.audit_schemas import AuditLogResponse, PaginatedAuditLogs
from services.audit_service import AuditLogService
from utils.responses import success

router = APIRouter(prefix="/api/v1/audit-logs", tags=["Audit Logs"])


@router.get("", response_model=dict)
def search_audit_logs(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=30, ge=1, le=100),
    action: str | None = None,
    entity_type: str | None = None,
    user_id: int | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    db: Session = Depends(get_db),
    _owner: User = Depends(require_roles(RoleName.OWNER)),
):
    items, total = AuditLogService(db).search(
        page=page,
        page_size=page_size,
        action=action,
        entity_type=entity_type,
        user_id=user_id,
        date_from=date_from,
        date_to=date_to,
    )
    body = PaginatedAuditLogs(
        total=total, page=page, page_size=page_size, items=[AuditLogResponse.model_validate(a) for a in items]
    )
    return success(body.model_dump())
