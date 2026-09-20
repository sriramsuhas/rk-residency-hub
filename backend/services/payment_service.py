"""
Business logic for mock payments. Payments always succeed here — there is
no real payment gateway — but the flow (create payment -> confirm booking ->
generate invoice) mirrors a real one so the architecture stays honest.
"""
import secrets
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from models.enums import BookingStatus, NotificationType, PaymentStatus
from models.payment import Payment
from repositories.audit_log_repository import AuditLogRepository
from repositories.booking_repository import BookingRepository
from repositories.payment_repository import PaymentRepository
from services.booking_service import BookingService
from services.invoice_service import InvoiceService
from services.notification_service import NotificationService
from utils.email import send_email
from utils.email_templates import booking_confirmation_email
from utils.enum_utils import status_label
from utils.exceptions import NotFoundError, UnauthorizedError, ValidationAppError


class PaymentService:
    def __init__(self, db: Session):
        self.db = db
        self.payments = PaymentRepository(db)
        self.bookings = BookingRepository(db)
        self.booking_service = BookingService(db)
        self.invoice_service = InvoiceService(db)
        self.notifications = NotificationService(db)
        self.audit = AuditLogRepository(db)

    def pay_for_booking(self, booking_id: int, method: str, customer_id: int) -> Payment:
        booking = self.bookings.get_by_id(booking_id)
        if booking is None:
            raise NotFoundError("Booking not found")
        if booking.customer_id != customer_id:
            raise UnauthorizedError("You can only pay for your own bookings")
        if booking.status != BookingStatus.PENDING_PAYMENT.value:
            raise ValidationAppError(
                f"This booking is not awaiting payment (current status: {status_label(booking.status)})"
            )

        payment = Payment(
            booking_id=booking.id,
            amount=booking.total_amount,
            method=method,
            status=PaymentStatus.SUCCESS,
            transaction_reference=f"MOCK-{secrets.token_hex(6).upper()}",
        )
        payment = self.payments.create(payment)

        self.booking_service.mark_confirmed(booking.id)
        self.invoice_service.generate_invoice(booking, payment)

        self.notifications.notify(
            user_id=customer_id,
            title="Booking confirmed",
            message=f"Your payment for Room {booking.room.room_number} was successful. Your booking is now confirmed.",
            notification_type=NotificationType.BOOKING,
            related_entity_type="Booking",
            related_entity_id=booking.id,
        )

        subject, body = booking_confirmation_email(
            booking.customer.full_name,
            booking.room.room_number,
            booking.check_in_date.isoformat(),
            booking.check_out_date.isoformat(),
            float(booking.total_amount),
        )
        send_email(booking.customer.email, subject, body)

        self.audit.log(
            action="PAYMENT_SUCCEEDED", user_id=customer_id, entity_type="Payment", entity_id=payment.id
        )
        return payment

    def get_payment(self, payment_id: int) -> Payment:
        payment = self.payments.get_by_id(payment_id)
        if payment is None:
            raise NotFoundError("Payment not found")
        return payment

    def get_payment_for_viewer(self, payment_id: int, requester_id: int, requester_role: str) -> Payment:
        payment = self.get_payment(payment_id)
        is_owner = payment.booking.customer_id == requester_id
        is_staff = requester_role in ("RECEPTION", "OWNER")
        if not (is_owner or is_staff):
            raise UnauthorizedError("You do not have access to this payment")
        return payment

    def list_my_payments(self, customer_id: int, page: int, page_size: int):
        return self.payments.list_for_customer(customer_id, page, page_size)

    def refund_payment(self, payment_id: int, actor_id: int, reason: str | None) -> Payment:
        payment = self.get_payment(payment_id)

        if payment.status != PaymentStatus.SUCCESS.value:
            raise ValidationAppError(f"Only SUCCESS payments can be refunded (this one is {status_label(payment.status)})")
        if payment.booking.status != BookingStatus.CANCELLED.value:
            raise ValidationAppError("A payment can only be refunded once its booking is cancelled")

        payment.status = PaymentStatus.REFUNDED
        payment.refunded_at = datetime.now(timezone.utc)
        payment.refund_reason = reason
        self.payments.update(payment)

        self.notifications.notify(
            user_id=payment.booking.customer_id,
            title="Refund processed",
            message=f"Your payment of Rs. {float(payment.amount):.2f} has been refunded.",
            notification_type=NotificationType.PAYMENT,
            related_entity_type="Payment",
            related_entity_id=payment.id,
        )

        self.audit.log(
            action="PAYMENT_REFUNDED", user_id=actor_id, entity_type="Payment", entity_id=payment.id
        )
        return payment
