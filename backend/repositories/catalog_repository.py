"""Direct database access for the catalog lookup tables: floors, room types, amenities."""
from sqlalchemy import select
from sqlalchemy.orm import Session

from models.amenity import Amenity
from models.floor import Floor
from models.room_type import RoomType


class FloorRepository:
    def __init__(self, db: Session):
        self.db = db

    def list_all(self) -> list[Floor]:
        return list(self.db.execute(select(Floor).order_by(Floor.floor_number)).scalars().all())

    def get_by_id(self, floor_id: int) -> Floor | None:
        return self.db.get(Floor, floor_id)

    def get_by_name_or_number(self, name: str, floor_number: int) -> Floor | None:
        stmt = select(Floor).where((Floor.name == name) | (Floor.floor_number == floor_number))
        return self.db.execute(stmt).scalar_one_or_none()

    def create(self, floor: Floor) -> Floor:
        self.db.add(floor)
        self.db.commit()
        self.db.refresh(floor)
        return floor

    def update(self, floor: Floor) -> Floor:
        self.db.commit()
        self.db.refresh(floor)
        return floor

    def delete(self, floor: Floor) -> None:
        self.db.delete(floor)
        self.db.commit()

    def has_rooms(self, floor_id: int) -> bool:
        from models.room import Room

        stmt = select(Room.id).where(Room.floor_id == floor_id).limit(1)
        return self.db.execute(stmt).scalar_one_or_none() is not None


class RoomTypeRepository:
    def __init__(self, db: Session):
        self.db = db

    def list_all(self) -> list[RoomType]:
        return list(self.db.execute(select(RoomType).order_by(RoomType.name)).scalars().all())

    def get_by_id(self, room_type_id: int) -> RoomType | None:
        return self.db.get(RoomType, room_type_id)

    def get_by_name(self, name: str) -> RoomType | None:
        stmt = select(RoomType).where(RoomType.name == name)
        return self.db.execute(stmt).scalar_one_or_none()

    def create(self, room_type: RoomType) -> RoomType:
        self.db.add(room_type)
        self.db.commit()
        self.db.refresh(room_type)
        return room_type

    def update(self, room_type: RoomType) -> RoomType:
        self.db.commit()
        self.db.refresh(room_type)
        return room_type

    def delete(self, room_type: RoomType) -> None:
        self.db.delete(room_type)
        self.db.commit()

    def has_rooms(self, room_type_id: int) -> bool:
        from models.room import Room

        stmt = select(Room.id).where(Room.room_type_id == room_type_id).limit(1)
        return self.db.execute(stmt).scalar_one_or_none() is not None


class AmenityRepository:
    def __init__(self, db: Session):
        self.db = db

    def list_all(self) -> list[Amenity]:
        return list(self.db.execute(select(Amenity).order_by(Amenity.name)).scalars().all())

    def get_by_id(self, amenity_id: int) -> Amenity | None:
        return self.db.get(Amenity, amenity_id)

    def get_by_ids(self, amenity_ids: list[int]) -> list[Amenity]:
        if not amenity_ids:
            return []
        stmt = select(Amenity).where(Amenity.id.in_(amenity_ids))
        return list(self.db.execute(stmt).scalars().all())

    def get_by_name(self, name: str) -> Amenity | None:
        stmt = select(Amenity).where(Amenity.name == name)
        return self.db.execute(stmt).scalar_one_or_none()

    def create(self, amenity: Amenity) -> Amenity:
        self.db.add(amenity)
        self.db.commit()
        self.db.refresh(amenity)
        return amenity

    def delete(self, amenity: Amenity) -> None:
        self.db.delete(amenity)
        self.db.commit()
