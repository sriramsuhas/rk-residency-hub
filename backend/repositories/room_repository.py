"""Direct database access for rooms and their images. Search/filter logic lives here as query-building only."""
from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from models.amenity import Amenity
from models.room import Room, room_amenities
from models.room_image import RoomImage


class RoomRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, room_id: int) -> Room | None:
        stmt = (
            select(Room)
            .options(
                joinedload(Room.floor),
                joinedload(Room.room_type),
                joinedload(Room.amenities),
                joinedload(Room.images),
            )
            .where(Room.id == room_id)
        )
        return self.db.execute(stmt).unique().scalar_one_or_none()

    def get_by_room_number(self, room_number: str) -> Room | None:
        stmt = select(Room).where(Room.room_number == room_number)
        return self.db.execute(stmt).scalar_one_or_none()

    def create(self, room: Room) -> Room:
        self.db.add(room)
        self.db.commit()
        self.db.refresh(room)
        return room

    def update(self, room: Room) -> Room:
        self.db.commit()
        self.db.refresh(room)
        return room

    def search(
        self,
        page: int,
        page_size: int,
        search: str | None = None,
        floor_id: int | None = None,
        room_type_id: int | None = None,
        min_price: float | None = None,
        max_price: float | None = None,
        capacity: int | None = None,
        availability_status: str | None = None,
        amenity_ids: list[int] | None = None,
        sort_by: str = "room_number",
        active_only: bool = True,
    ) -> tuple[list[Room], int]:
        stmt = select(Room).options(
            joinedload(Room.floor), joinedload(Room.room_type), joinedload(Room.images)
        )
        count_stmt = select(func.count(func.distinct(Room.id))).select_from(Room)

        conditions = []
        if active_only:
            conditions.append(Room.is_active.is_(True))
        if search:
            like = f"%{search.lower()}%"
            conditions.append(
                func.lower(Room.room_number).like(like) | func.lower(Room.description).like(like)
            )
        if floor_id:
            conditions.append(Room.floor_id == floor_id)
        if room_type_id:
            conditions.append(Room.room_type_id == room_type_id)
        if min_price is not None:
            conditions.append(Room.price_per_night >= min_price)
        if max_price is not None:
            conditions.append(Room.price_per_night <= max_price)
        if capacity is not None:
            conditions.append(Room.capacity >= capacity)
        if availability_status:
            conditions.append(Room.availability_status == availability_status)

        for condition in conditions:
            stmt = stmt.where(condition)
            count_stmt = count_stmt.where(condition)

        if amenity_ids:
            # A room must have ALL requested amenities.
            amenity_stmt = (
                select(room_amenities.c.room_id)
                .where(room_amenities.c.amenity_id.in_(amenity_ids))
                .group_by(room_amenities.c.room_id)
                .having(func.count(func.distinct(room_amenities.c.amenity_id)) == len(amenity_ids))
            )
            stmt = stmt.where(Room.id.in_(amenity_stmt))
            count_stmt = count_stmt.where(Room.id.in_(amenity_stmt))

        sort_map = {
            "price_asc": Room.price_per_night.asc(),
            "price_desc": Room.price_per_night.desc(),
            "room_number": Room.room_number.asc(),
        }
        stmt = stmt.order_by(sort_map.get(sort_by, Room.room_number.asc()))
        stmt = stmt.offset((page - 1) * page_size).limit(page_size)

        total = self.db.execute(count_stmt).scalar_one()
        items = list(self.db.execute(stmt).unique().scalars().all())
        return items, total

    def set_amenities(self, room: Room, amenities: list[Amenity]) -> Room:
        room.amenities = amenities
        self.db.commit()
        self.db.refresh(room)
        return room


class RoomImageRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, image: RoomImage) -> RoomImage:
        self.db.add(image)
        self.db.commit()
        self.db.refresh(image)
        return image

    def get_by_id(self, image_id: int) -> RoomImage | None:
        return self.db.get(RoomImage, image_id)

    def delete(self, image: RoomImage) -> None:
        self.db.delete(image)
        self.db.commit()

    def unset_other_primaries(self, room_id: int) -> None:
        stmt = select(RoomImage).where(RoomImage.room_id == room_id, RoomImage.is_primary.is_(True))
        for img in self.db.execute(stmt).scalars().all():
            img.is_primary = False
        self.db.commit()
