"""Direct database access for payments and invoices."""
from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from models.invoice import Invoice
from models.payment import Payment


class PaymentRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, payment_id: int) -> Payment | None:
        return self.db.get(Payment, payment_id)

    def get_by_booking_id(self, booking_id: int) -> Payment | None:
        stmt = select(Payment).where(Payment.booking_id == booking_id).order_by(Payment.id.desc())
        return self.db.execute(stmt).scalars().first()

    def create(self, payment: Payment) -> Payment:
        self.db.add(payment)
        self.db.commit()
        self.db.refresh(payment)
        return payment

    def update(self, payment: Payment) -> Payment:
        self.db.commit()
        self.db.refresh(payment)
        return payment

    def list_for_customer(self, customer_id: int, page: int, page_size: int) -> tuple[list[Payment], int]:
        from models.booking import Booking

        stmt = (
            select(Payment)
            .join(Booking, Payment.booking_id == Booking.id)
            .where(Booking.customer_id == customer_id)
        )
        count_stmt = (
            select(func.count())
            .select_from(Payment)
            .join(Booking, Payment.booking_id == Booking.id)
            .where(Booking.customer_id == customer_id)
        )
        total = self.db.execute(count_stmt).scalar_one()
        stmt = stmt.order_by(Payment.paid_at.desc()).offset((page - 1) * page_size).limit(page_size)
        items = list(self.db.execute(stmt).scalars().all())
        return items, total


class InvoiceRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_booking_id(self, booking_id: int) -> Invoice | None:
        stmt = select(Invoice).where(Invoice.booking_id == booking_id)
        return self.db.execute(stmt).scalar_one_or_none()

    def get_by_id(self, invoice_id: int) -> Invoice | None:
        return self.db.get(Invoice, invoice_id)

    def count_all(self) -> int:
        return self.db.execute(select(func.count()).select_from(Invoice)).scalar_one()

    def create(self, invoice: Invoice) -> Invoice:
        self.db.add(invoice)
        self.db.commit()
        self.db.refresh(invoice)
        return invoice
