"""Business logic for the catalog lookup tables: floors, room types, amenities."""
from sqlalchemy.orm import Session

from models.amenity import Amenity
from models.floor import Floor
from models.room_type import RoomType
from repositories.catalog_repository import AmenityRepository, FloorRepository, RoomTypeRepository
from schemas.catalog_schemas import (
    AmenityCreateRequest,
    FloorCreateRequest,
    FloorUpdateRequest,
    RoomTypeCreateRequest,
    RoomTypeUpdateRequest,
)
from utils.exceptions import ConflictError, NotFoundError, ValidationAppError


class FloorService:
    def __init__(self, db: Session):
        self.repo = FloorRepository(db)

    def list_floors(self) -> list[Floor]:
        return self.repo.list_all()

    def create_floor(self, payload: FloorCreateRequest) -> Floor:
        if self.repo.get_by_name_or_number(payload.name, payload.floor_number):
            raise ConflictError("A floor with this name or number already exists")
        floor = Floor(name=payload.name, floor_number=payload.floor_number, description=payload.description)
        return self.repo.create(floor)

    def update_floor(self, floor_id: int, payload: FloorUpdateRequest) -> Floor:
        floor = self.repo.get_by_id(floor_id)
        if floor is None:
            raise NotFoundError("Floor not found")
        if payload.name is not None:
            floor.name = payload.name
        if payload.floor_number is not None:
            floor.floor_number = payload.floor_number
        if payload.description is not None:
            floor.description = payload.description
        return self.repo.update(floor)

    def delete_floor(self, floor_id: int) -> None:
        floor = self.repo.get_by_id(floor_id)
        if floor is None:
            raise NotFoundError("Floor not found")
        if self.repo.has_rooms(floor_id):
            raise ValidationAppError("Cannot delete a floor that still has rooms assigned to it")
        self.repo.delete(floor)


class RoomTypeService:
    def __init__(self, db: Session):
        self.repo = RoomTypeRepository(db)

    def list_room_types(self) -> list[RoomType]:
        return self.repo.list_all()

    def create_room_type(self, payload: RoomTypeCreateRequest) -> RoomType:
        if self.repo.get_by_name(payload.name):
            raise ConflictError("A room type with this name already exists")
        room_type = RoomType(
            name=payload.name,
            description=payload.description,
            base_price=payload.base_price,
            max_occupancy=payload.max_occupancy,
        )
        return self.repo.create(room_type)

    def update_room_type(self, room_type_id: int, payload: RoomTypeUpdateRequest) -> RoomType:
        room_type = self.repo.get_by_id(room_type_id)
        if room_type is None:
            raise NotFoundError("Room type not found")
        if payload.name is not None:
            room_type.name = payload.name
        if payload.description is not None:
            room_type.description = payload.description
        if payload.base_price is not None:
            room_type.base_price = payload.base_price
        if payload.max_occupancy is not None:
            room_type.max_occupancy = payload.max_occupancy
        return self.repo.update(room_type)

    def delete_room_type(self, room_type_id: int) -> None:
        room_type = self.repo.get_by_id(room_type_id)
        if room_type is None:
            raise NotFoundError("Room type not found")
        if self.repo.has_rooms(room_type_id):
            raise ValidationAppError("Cannot delete a room type that still has rooms assigned to it")
        self.repo.delete(room_type)


class AmenityService:
    def __init__(self, db: Session):
        self.repo = AmenityRepository(db)

    def list_amenities(self) -> list[Amenity]:
        return self.repo.list_all()

    def create_amenity(self, payload: AmenityCreateRequest) -> Amenity:
        if self.repo.get_by_name(payload.name):
            raise ConflictError("An amenity with this name already exists")
        amenity = Amenity(name=payload.name, icon=payload.icon)
        return self.repo.create(amenity)

    def delete_amenity(self, amenity_id: int) -> None:
        amenity = self.repo.get_by_id(amenity_id)
        if amenity is None:
            raise NotFoundError("Amenity not found")
        self.repo.delete(amenity)
