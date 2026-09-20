"""HTTP routes for the booking engine."""
from datetime import date

from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from auth.dependencies import get_current_user, require_roles
from config.settings import settings
from database.session import get_db
from models.enums import RoleName
from models.user import User
from schemas.booking_schemas import (
    AssignRoomRequest,
    BookingCancelRequest,
    BookingCreateRequest,
    BookingResponse,
    PaginatedBookings,
)
from schemas.payment_schemas import InvoiceResponse, PaymentCreateRequest, PaymentResponse
from services.booking_service import BookingService
from services.invoice_service import InvoiceService
from services.payment_service import PaymentService
from utils.exceptions import NotFoundError
from utils.responses import success

router = APIRouter(prefix="/api/v1/bookings", tags=["Bookings"])


@router.post("", response_model=dict, status_code=status.HTTP_201_CREATED)
def create_booking(
    payload: BookingCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(RoleName.CUSTOMER)),
):
    booking = BookingService(db).create_booking(payload, current_user.id)
    return success(BookingResponse.model_validate(booking).model_dump(), "Booking confirmed")


@router.get("/me", response_model=dict)
def my_bookings(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=50),
    status_filter: str | None = Query(default=None, alias="status"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(RoleName.CUSTOMER)),
):
    items, total = BookingService(db).list_my_bookings(current_user.id, page, page_size, status_filter)
    body = PaginatedBookings(
        total=total, page=page, page_size=page_size, items=[BookingResponse.model_validate(b) for b in items]
    )
    return success(body.model_dump())


@router.get("", response_model=dict)
def search_bookings(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    status_filter: str | None = Query(default=None, alias="status"),
    room_id: int | None = None,
    customer_id: int | None = None,
    check_in_from: date | None = None,
    check_in_to: date | None = None,
    db: Session = Depends(get_db),
    _staff: User = Depends(require_roles(RoleName.RECEPTION, RoleName.OWNER)),
):
    items, total = BookingService(db).search_bookings(
        page=page,
        page_size=page_size,
        status_filter=status_filter,
        room_id=room_id,
        customer_id=customer_id,
        check_in_from=check_in_from,
        check_in_to=check_in_to,
    )
    body = PaginatedBookings(
        total=total, page=page, page_size=page_size, items=[BookingResponse.model_validate(b) for b in items]
    )
    return success(body.model_dump())


@router.get("/{booking_id}", response_model=dict)
def get_booking(
    booking_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    booking = BookingService(db).get_booking_for_viewer(booking_id, current_user.id, current_user.role.name)
    return success(BookingResponse.model_validate(booking).model_dump())


@router.post("/{booking_id}/cancel", response_model=dict)
def cancel_booking(
    booking_id: int,
    payload: BookingCancelRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    booking = BookingService(db).cancel_booking(
        booking_id, current_user.id, current_user.role.name, payload.reason
    )
    return success(BookingResponse.model_validate(booking).model_dump(), "Booking cancelled")


@router.post("/{booking_id}/check-in", response_model=dict)
def check_in(
    booking_id: int,
    db: Session = Depends(get_db),
    actor: User = Depends(require_roles(RoleName.RECEPTION, RoleName.OWNER)),
):
    booking = BookingService(db).check_in(booking_id, actor.id)
    return success(BookingResponse.model_validate(booking).model_dump(), "Guest checked in")


@router.post("/{booking_id}/check-out", response_model=dict)
def check_out(
    booking_id: int,
    db: Session = Depends(get_db),
    actor: User = Depends(require_roles(RoleName.RECEPTION, RoleName.OWNER)),
):
    booking = BookingService(db).check_out(booking_id, actor.id)
    return success(BookingResponse.model_validate(booking).model_dump(), "Guest checked out")


@router.patch("/{booking_id}/assign-room", response_model=dict)
def assign_room(
    booking_id: int,
    payload: AssignRoomRequest,
    db: Session = Depends(get_db),
    actor: User = Depends(require_roles(RoleName.RECEPTION, RoleName.OWNER)),
):
    booking = BookingService(db).assign_room(booking_id, payload.room_id, actor.id)
    return success(BookingResponse.model_validate(booking).model_dump(), "Room reassigned")


@router.post("/{booking_id}/pay", response_model=dict)
def pay_for_booking(
    booking_id: int,
    payload: PaymentCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(RoleName.CUSTOMER)),
):
    payment = PaymentService(db).pay_for_booking(booking_id, payload.method.value, current_user.id)
    return success(PaymentResponse.model_validate(payment).model_dump(), "Payment successful")


@router.get("/{booking_id}/invoice", response_model=dict)
def get_invoice(
    booking_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Reuses booking visibility rules: owner of the booking, or staff.
    BookingService(db).get_booking_for_viewer(booking_id, current_user.id, current_user.role.name)
    invoice = InvoiceService(db).get_by_booking(booking_id)
    return success(InvoiceResponse.model_validate(invoice).model_dump())


@router.get("/{booking_id}/invoice/pdf")
def download_invoice_pdf(
    booking_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    BookingService(db).get_booking_for_viewer(booking_id, current_user.id, current_user.role.name)
    invoice = InvoiceService(db).get_by_booking(booking_id)
    if not invoice.pdf_path:
        raise NotFoundError("Invoice PDF is not available")

    # invoice.pdf_path is stored as a URL path like /uploads/invoices/X.pdf;
    # strip the leading /uploads/ to resolve it against the upload directory.
    relative_path = invoice.pdf_path.removeprefix("/uploads/")
    filesystem_path = f"{settings.upload_dir}/{relative_path}"
    return FileResponse(filesystem_path, media_type="application/pdf", filename=f"{invoice.invoice_number}.pdf")
