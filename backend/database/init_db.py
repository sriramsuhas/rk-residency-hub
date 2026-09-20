"""
One-time setup script: creates all tables and seeds the fixed roles plus
a default OWNER account so the system is usable immediately after install.

Run with:
    python -m database.init_db
"""
import models  # noqa: F401  (registers all models on Base.metadata)
from auth.hashing import hash_password
from database.session import Base, SessionLocal, engine
from models.amenity import Amenity
from models.enums import RoleName
from models.floor import Floor
from models.role import Role
from models.room import Room
from models.room_type import RoomType
from models.user import User

DEFAULT_OWNER_EMAIL = "owner@rkresidency.com"
DEFAULT_OWNER_PASSWORD = "Owner@12345"  # noqa: S105 — dev-only seed credential, change after first login


def seed_roles(db) -> dict[str, Role]:
    existing = {r.name: r for r in db.query(Role).all()}
    descriptions = {
        RoleName.CUSTOMER.value: "Guests who browse rooms and make bookings",
        RoleName.RECEPTION.value: "Front-desk staff managing check-ins/outs and bookings",
        RoleName.HOUSEKEEPING.value: "Housekeeping and maintenance staff",
        RoleName.OWNER.value: "Property owner / admin with full access",
    }
    for name, desc in descriptions.items():
        if name not in existing:
            role = Role(name=name, description=desc)
            db.add(role)
            existing[name] = role
    db.commit()
    return {r.name: r for r in db.query(Role).all()}


def seed_default_owner(db, roles: dict[str, Role]) -> None:
    existing = db.query(User).filter(User.email == DEFAULT_OWNER_EMAIL).first()
    if existing:
        return
    owner = User(
        full_name="RK Residency Hub Owner",
        email=DEFAULT_OWNER_EMAIL,
        hashed_password=hash_password(DEFAULT_OWNER_PASSWORD),
        role_id=roles[RoleName.OWNER.value].id,
        is_active=True,
    )
    db.add(owner)
    db.commit()


def seed_catalog(db) -> None:
    """Demo inventory so the app is browsable immediately after install."""
    if db.query(Floor).count() > 0:
        return  # already seeded

    floors = [
        Floor(name="Ground Floor", floor_number=0, description="Lobby level"),
        Floor(name="Floor 1", floor_number=1),
        Floor(name="Floor 2", floor_number=2),
    ]
    db.add_all(floors)
    db.flush()

    room_types = [
        RoomType(name="Standard", description="Cozy and comfortable", base_price=1800, max_occupancy=2),
        RoomType(name="Deluxe", description="Extra space with a view", base_price=2800, max_occupancy=3),
        RoomType(name="Suite", description="Separate living area", base_price=4500, max_occupancy=4),
    ]
    db.add_all(room_types)
    db.flush()

    amenities = [
        Amenity(name="WiFi", icon="wifi"),
        Amenity(name="Air Conditioning", icon="ac"),
        Amenity(name="TV", icon="tv"),
        Amenity(name="Balcony", icon="balcony"),
        Amenity(name="Mini Fridge", icon="fridge"),
    ]
    db.add_all(amenities)
    db.flush()

    sample_rooms = [
        Room(
            room_number="101",
            floor_id=floors[1].id,
            room_type_id=room_types[0].id,
            price_per_night=room_types[0].base_price,
            capacity=room_types[0].max_occupancy,
            description="A bright standard room facing the courtyard.",
            amenities=[amenities[0], amenities[1]],
        ),
        Room(
            room_number="102",
            floor_id=floors[1].id,
            room_type_id=room_types[1].id,
            price_per_night=room_types[1].base_price,
            capacity=room_types[1].max_occupancy,
            description="Deluxe room with a street-facing balcony.",
            amenities=[amenities[0], amenities[1], amenities[2], amenities[3]],
        ),
        Room(
            room_number="201",
            floor_id=floors[2].id,
            room_type_id=room_types[2].id,
            price_per_night=room_types[2].base_price,
            capacity=room_types[2].max_occupancy,
            description="Top-floor suite with a separate sitting area.",
            amenities=amenities,
        ),
    ]
    db.add_all(sample_rooms)
    db.commit()


def main() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        roles = seed_roles(db)
        seed_default_owner(db, roles)
        seed_catalog(db)
        print("Database initialized: tables created, roles seeded, default owner ready.")
        print(f"  Owner login: {DEFAULT_OWNER_EMAIL} / {DEFAULT_OWNER_PASSWORD}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
