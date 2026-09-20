from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.session import Base


class Floor(Base):
    __tablename__ = "floors"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    floor_number: Mapped[int] = mapped_column(Integer, unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(String(255), nullable=True)

    rooms: Mapped[list["Room"]] = relationship(back_populates="floor")

    def __repr__(self) -> str:
        return f"<Floor {self.name}>"
