"""Response models for the audit log read API."""
from datetime import datetime

from pydantic import BaseModel


class AuditLogUserSummary(BaseModel):
    id: int
    full_name: str
    email: str

    model_config = {"from_attributes": True}


class AuditLogResponse(BaseModel):
    id: int
    action: str
    entity_type: str | None
    entity_id: int | None
    details: str | None
    created_at: datetime
    user: AuditLogUserSummary | None

    model_config = {"from_attributes": True}


class PaginatedAuditLogs(BaseModel):
    total: int
    page: int
    page_size: int
    items: list[AuditLogResponse]
