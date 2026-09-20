"""HTTP routes for payments."""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from auth.dependencies import get_current_user, require_roles
from database.session import get_db
from models.enums import RoleName
from models.user import User
from schemas.payment_schemas import PaginatedPayments, PaymentResponse, RefundRequest
from services.payment_service import PaymentService
from utils.responses import success

router = APIRouter(prefix="/api/v1/payments", tags=["Payments"])


@router.get("/me", response_model=dict)
def my_payments(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=50),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(RoleName.CUSTOMER)),
):
    items, total = PaymentService(db).list_my_payments(current_user.id, page, page_size)
    body = PaginatedPayments(
        total=total, page=page, page_size=page_size, items=[PaymentResponse.model_validate(p) for p in items]
    )
    return success(body.model_dump())


@router.get("/{payment_id}", response_model=dict)
def get_payment(
    payment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    payment = PaymentService(db).get_payment_for_viewer(payment_id, current_user.id, current_user.role.name)
    return success(PaymentResponse.model_validate(payment).model_dump())


@router.post("/{payment_id}/refund", response_model=dict)
def refund_payment(
    payment_id: int,
    payload: RefundRequest,
    db: Session = Depends(get_db),
    actor: User = Depends(require_roles(RoleName.RECEPTION, RoleName.OWNER)),
):
    payment = PaymentService(db).refund_payment(payment_id, actor.id, payload.reason)
    return success(PaymentResponse.model_validate(payment).model_dump(), "Payment refunded")
