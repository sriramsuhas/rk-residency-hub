from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.session import Base


class Amenity(Base):
    __tablename__ = "amenities"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(60), unique=True, nullable=False)
    icon: Mapped[str | None] = mapped_column(String(50), nullable=True)

    rooms: Mapped[list["Room"]] = relationship(secondary="room_amenities", back_populates="amenities")

    def __repr__(self) -> str:
        return f"<Amenity {self.name}>"
