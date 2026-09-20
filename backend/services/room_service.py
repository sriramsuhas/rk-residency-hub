"""Business logic for rooms: CRUD, search/filter, amenity assignment, and image uploads."""
from fastapi import UploadFile
from sqlalchemy.orm import Session

from models.room import Room
from models.room_image import RoomImage
from repositories.audit_log_repository import AuditLogRepository
from repositories.catalog_repository import AmenityRepository, FloorRepository, RoomTypeRepository
from repositories.room_repository import RoomImageRepository, RoomRepository
from schemas.room_schemas import RoomCreateRequest, RoomUpdateRequest
from utils.exceptions import ConflictError, NotFoundError, ValidationAppError
from utils.uploads import save_uploaded_image


class RoomService:
    def __init__(self, db: Session):
        self.db = db
        self.rooms = RoomRepository(db)
        self.floors = FloorRepository(db)
        self.room_types = RoomTypeRepository(db)
        self.amenities = AmenityRepository(db)
        self.images = RoomImageRepository(db)
        self.audit = AuditLogRepository(db)

    def get_room(self, room_id: int) -> Room:
        room = self.rooms.get_by_id(room_id)
        if room is None:
            raise NotFoundError("Room not found")
        return room

    def search_rooms(self, **kwargs):
        return self.rooms.search(**kwargs)

    def create_room(self, payload: RoomCreateRequest, actor_id: int) -> Room:
        if self.rooms.get_by_room_number(payload.room_number):
            raise ConflictError("A room with this number already exists")
        if self.floors.get_by_id(payload.floor_id) is None:
            raise NotFoundError("Floor not found")
        if self.room_types.get_by_id(payload.room_type_id) is None:
            raise NotFoundError("Room type not found")

        amenities = self.amenities.get_by_ids(payload.amenity_ids) if payload.amenity_ids else []
        if len(amenities) != len(set(payload.amenity_ids)):
            raise ValidationAppError("One or more amenity IDs are invalid")

        room = Room(
            room_number=payload.room_number,
            floor_id=payload.floor_id,
            room_type_id=payload.room_type_id,
            price_per_night=payload.price_per_night,
            capacity=payload.capacity,
            description=payload.description,
            amenities=amenities,
        )
        room = self.rooms.create(room)
        self.audit.log(action="ROOM_CREATED", user_id=actor_id, entity_type="Room", entity_id=room.id)
        return self.get_room(room.id)

    def update_room(self, room_id: int, payload: RoomUpdateRequest, actor_id: int) -> Room:
        room = self.get_room(room_id)

        if payload.room_number is not None and payload.room_number != room.room_number:
            if self.rooms.get_by_room_number(payload.room_number):
                raise ConflictError("A room with this number already exists")
            room.room_number = payload.room_number
        if payload.floor_id is not None:
            if self.floors.get_by_id(payload.floor_id) is None:
                raise NotFoundError("Floor not found")
            room.floor_id = payload.floor_id
        if payload.room_type_id is not None:
            if self.room_types.get_by_id(payload.room_type_id) is None:
                raise NotFoundError("Room type not found")
            room.room_type_id = payload.room_type_id
        if payload.price_per_night is not None:
            room.price_per_night = payload.price_per_night
        if payload.capacity is not None:
            room.capacity = payload.capacity
        if payload.description is not None:
            room.description = payload.description

        self.rooms.update(room)
        self.audit.log(action="ROOM_UPDATED", user_id=actor_id, entity_type="Room", entity_id=room.id)
        return self.get_room(room.id)

    def deactivate_room(self, room_id: int, actor_id: int) -> Room:
        room = self.get_room(room_id)
        room.is_active = False
        self.rooms.update(room)
        self.audit.log(action="ROOM_DEACTIVATED", user_id=actor_id, entity_type="Room", entity_id=room.id)
        return room

    def update_availability(self, room_id: int, status_value: str, actor_id: int) -> Room:
        room = self.get_room(room_id)
        room.availability_status = status_value
        self.rooms.update(room)
        self.audit.log(
            action="ROOM_AVAILABILITY_UPDATED",
            user_id=actor_id,
            entity_type="Room",
            entity_id=room.id,
            details=status_value,
        )
        return self.get_room(room.id)

    def update_cleaning_status(self, room_id: int, status_value: str, actor_id: int) -> Room:
        room = self.get_room(room_id)
        room.cleaning_status = status_value
        self.rooms.update(room)
        self.audit.log(
            action="ROOM_CLEANING_STATUS_UPDATED",
            user_id=actor_id,
            entity_type="Room",
            entity_id=room.id,
            details=status_value,
        )
        return self.get_room(room.id)

    def set_amenities(self, room_id: int, amenity_ids: list[int], actor_id: int) -> Room:
        room = self.get_room(room_id)
        amenities = self.amenities.get_by_ids(amenity_ids)
        if len(amenities) != len(set(amenity_ids)):
            raise ValidationAppError("One or more amenity IDs are invalid")
        self.rooms.set_amenities(room, amenities)
        self.audit.log(action="ROOM_AMENITIES_UPDATED", user_id=actor_id, entity_type="Room", entity_id=room_id)
        return self.get_room(room_id)

    def add_image(self, room_id: int, file: UploadFile, is_primary: bool, actor_id: int) -> Room:
        room = self.get_room(room_id)
        image_url = save_uploaded_image(file, "room_images")

        if is_primary:
            self.images.unset_other_primaries(room_id)

        image = RoomImage(room_id=room_id, image_url=image_url, is_primary=is_primary)
        self.images.create(image)
        self.audit.log(action="ROOM_IMAGE_ADDED", user_id=actor_id, entity_type="Room", entity_id=room_id)
        return self.get_room(room_id)

    def delete_image(self, room_id: int, image_id: int, actor_id: int) -> Room:
        image = self.images.get_by_id(image_id)
        if image is None or image.room_id != room_id:
            raise NotFoundError("Image not found for this room")
        self.images.delete(image)
        self.audit.log(action="ROOM_IMAGE_DELETED", user_id=actor_id, entity_type="Room", entity_id=room_id)
        return self.get_room(room_id)
