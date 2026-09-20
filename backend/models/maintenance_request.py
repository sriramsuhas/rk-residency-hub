from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.session import Base
from models.enums import MaintenanceCategory, MaintenancePriority, MaintenanceRequestStatus
from models.mixins import TimestampMixin


class MaintenanceRequest(Base, TimestampMixin):
    __tablename__ = "maintenance_requests"

    id: Mapped[int] = mapped_column(primary_key=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    room_id: Mapped[int] = mapped_column(ForeignKey("rooms.id"), nullable=False)
    booking_id: Mapped[int | None] = mapped_column(ForeignKey("bookings.id"), nullable=True)

    category: Mapped[str] = mapped_column(Enum(MaintenanceCategory, native_enum=False, length=20), nullable=False)
    priority: Mapped[str] = mapped_column(
        Enum(MaintenancePriority, native_enum=False, length=10),
        default=MaintenancePriority.MEDIUM,
        nullable=False,
    )
    description: Mapped[str] = mapped_column(Text, nullable=False)
    image_url: Mapped[str | None] = mapped_column(String(255), nullable=True)

    status: Mapped[str] = mapped_column(
        Enum(MaintenanceRequestStatus, native_enum=False, length=20),
        default=MaintenanceRequestStatus.PENDING,
        nullable=False,
    )
    assigned_staff_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    assigned_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    completion_image_url: Mapped[str | None] = mapped_column(String(255), nullable=True)
    remarks: Mapped[str | None] = mapped_column(Text, nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    cancelled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    customer: Mapped["User"] = relationship(foreign_keys=[customer_id])
    assigned_staff: Mapped["User | None"] = relationship(foreign_keys=[assigned_staff_id])
    room: Mapped["Room"] = relationship()
    booking: Mapped["Booking | None"] = relationship()

    def __repr__(self) -> str:
        return f"<MaintenanceRequest #{self.id} room={self.room_id} {self.status}>"
