"""Request/response models for mock payments and invoice generation."""
from datetime import datetime

from pydantic import BaseModel, Field

from models.enums import PaymentMethod, PaymentStatus


class PaymentCreateRequest(BaseModel):
    method: PaymentMethod


class RefundRequest(BaseModel):
    reason: str | None = Field(default=None, max_length=255)


class PaymentResponse(BaseModel):
    id: int
    booking_id: int
    amount: float
    method: PaymentMethod
    status: PaymentStatus
    transaction_reference: str
    paid_at: datetime
    refunded_at: datetime | None
    refund_reason: str | None

    model_config = {"from_attributes": True}


class PaginatedPayments(BaseModel):
    total: int
    page: int
    page_size: int
    items: list[PaymentResponse]


class InvoiceResponse(BaseModel):
    id: int
    booking_id: int
    payment_id: int
    invoice_number: str
    subtotal: float
    tax_amount: float
    total_amount: float
    issued_at: datetime

    model_config = {"from_attributes": True}
