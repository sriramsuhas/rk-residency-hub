from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.session import Base
from models.enums import PaymentMethod, PaymentStatus
from models.mixins import utcnow


class Payment(Base):
    __tablename__ = "payments"

    id: Mapped[int] = mapped_column(primary_key=True)
    booking_id: Mapped[int] = mapped_column(ForeignKey("bookings.id"), nullable=False)
    amount: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    method: Mapped[str] = mapped_column(Enum(PaymentMethod, native_enum=False, length=10), nullable=False)
    status: Mapped[str] = mapped_column(
        Enum(PaymentStatus, native_enum=False, length=10), default=PaymentStatus.SUCCESS, nullable=False
    )
    transaction_reference: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    paid_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    refunded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    refund_reason: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)

    booking: Mapped["Booking"] = relationship()

    def __repr__(self) -> str:
        return f"<Payment #{self.id} booking={self.booking_id} {self.status}>"
