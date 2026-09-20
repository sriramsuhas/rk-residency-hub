from sqlalchemy import Boolean, Enum, ForeignKey, Integer, Numeric, String, Table, Column
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.session import Base
from models.enums import AvailabilityStatus, CleaningStatus, RoomMaintenanceFlag
from models.mixins import TimestampMixin

room_amenities = Table(
    "room_amenities",
    Base.metadata,
    Column("room_id", ForeignKey("rooms.id"), primary_key=True),
    Column("amenity_id", ForeignKey("amenities.id"), primary_key=True),
)


class Room(Base, TimestampMixin):
    __tablename__ = "rooms"

    id: Mapped[int] = mapped_column(primary_key=True)
    room_number: Mapped[str] = mapped_column(String(10), unique=True, nullable=False, index=True)
    floor_id: Mapped[int] = mapped_column(ForeignKey("floors.id"), nullable=False)
    room_type_id: Mapped[int] = mapped_column(ForeignKey("room_types.id"), nullable=False)
    price_per_night: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    capacity: Mapped[int] = mapped_column(Integer, nullable=False)
    description: Mapped[str | None] = mapped_column(String(1000), nullable=True)

    availability_status: Mapped[str] = mapped_column(
        Enum(AvailabilityStatus, native_enum=False, length=20),
        default=AvailabilityStatus.AVAILABLE,
        nullable=False,
    )
    cleaning_status: Mapped[str] = mapped_column(
        Enum(CleaningStatus, native_enum=False, length=20), default=CleaningStatus.CLEAN, nullable=False
    )
    maintenance_status: Mapped[str] = mapped_column(
        Enum(RoomMaintenanceFlag, native_enum=False, length=20),
        default=RoomMaintenanceFlag.NONE,
        nullable=False,
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    floor: Mapped["Floor"] = relationship(back_populates="rooms")
    room_type: Mapped["RoomType"] = relationship(back_populates="rooms")
    amenities: Mapped[list["Amenity"]] = relationship(secondary=room_amenities, back_populates="rooms")
    images: Mapped[list["RoomImage"]] = relationship(back_populates="room", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Room {self.room_number}>"
