"""HTTP routes for report generation. Every endpoint streams back a file download."""
from datetime import date, datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.orm import Session

from auth.dependencies import require_roles
from database.session import get_db
from models.enums import RoleName
from models.user import User
from services.report_service import ReportService

router = APIRouter(prefix="/api/v1/reports", tags=["Reports"])


def _default_range(date_from, date_to):
    today = datetime.now(timezone.utc).date()
    return date_from or (today - timedelta(days=30)), date_to or today


def _file_response(content: bytes, media_type: str, filename: str) -> Response:
    return Response(
        content=content,
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/revenue")
def revenue_report(
    format: str = Query(default="csv", pattern="^(csv|pdf)$"),
    date_from: date | None = None,
    date_to: date | None = None,
    db: Session = Depends(get_db),
    _staff: User = Depends(require_roles(RoleName.RECEPTION, RoleName.OWNER)),
):
    date_from, date_to = _default_range(date_from, date_to)
    content, media_type, filename = ReportService(db).revenue_report(date_from, date_to, format)
    return _file_response(content, media_type, filename)


@router.get("/bookings")
def booking_report(
    format: str = Query(default="csv", pattern="^(csv|pdf)$"),
    date_from: date | None = None,
    date_to: date | None = None,
    status: str | None = None,
    db: Session = Depends(get_db),
    _staff: User = Depends(require_roles(RoleName.RECEPTION, RoleName.OWNER)),
):
    date_from, date_to = _default_range(date_from, date_to)
    content, media_type, filename = ReportService(db).booking_report(date_from, date_to, status, format)
    return _file_response(content, media_type, filename)


@router.get("/maintenance")
def maintenance_report(
    format: str = Query(default="csv", pattern="^(csv|pdf)$"),
    date_from: date | None = None,
    date_to: date | None = None,
    status: str | None = None,
    db: Session = Depends(get_db),
    _staff: User = Depends(require_roles(RoleName.RECEPTION, RoleName.OWNER)),
):
    date_from, date_to = _default_range(date_from, date_to)
    content, media_type, filename = ReportService(db).maintenance_report(date_from, date_to, status, format)
    return _file_response(content, media_type, filename)


@router.get("/occupancy")
def occupancy_report(
    format: str = Query(default="csv", pattern="^(csv|pdf)$"),
    date_from: date | None = None,
    date_to: date | None = None,
    db: Session = Depends(get_db),
    _staff: User = Depends(require_roles(RoleName.RECEPTION, RoleName.OWNER)),
):
    date_from, date_to = _default_range(date_from, date_to)
    content, media_type, filename = ReportService(db).occupancy_report(date_from, date_to, format)
    return _file_response(content, media_type, filename)


@router.get("/customers")
def customer_report(
    format: str = Query(default="csv", pattern="^(csv|pdf)$"),
    db: Session = Depends(get_db),
    _owner: User = Depends(require_roles(RoleName.OWNER)),
):
    content, media_type, filename = ReportService(db).customer_report(format)
    return _file_response(content, media_type, filename)
