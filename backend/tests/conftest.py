"""
Shared pytest fixtures.

Each test gets a fresh in-memory SQLite database (fast, fully isolated) with
the four roles pre-seeded. Production/dev always run on PostgreSQL — SQLite
here is purely a test-speed choice and never touches real data.
"""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import models  # noqa: F401 registers all models
from database.session import Base, get_db
from main import app
from models.enums import RoleName
from models.role import Role


@pytest.fixture()
def db_session():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)

    session = TestingSessionLocal()
    for role_name in RoleName:
        session.add(Role(name=role_name.value, description=role_name.value.title()))
    session.commit()

    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def client(db_session):
    from fastapi.testclient import TestClient

    from middleware.rate_limiter import auth_rate_limiter

    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    # The rate limiter is a module-level singleton keyed by client IP, and
    # TestClient requests all share one IP — without this override, running
    # the full suite would trip the real limiter and fail unrelated tests.
    # test_rate_limiting.py removes this override to test the real thing.
    app.dependency_overrides[auth_rate_limiter] = lambda: None
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture()
def register_and_login(client):
    """Helper: registers a CUSTOMER and returns (access_token, refresh_token, user_json)."""

    def _do(email="test.customer@example.com", password="SecurePass1"):
        client.post(
            "/api/v1/auth/register",
            json={"full_name": "Test Customer", "email": email, "password": password},
        )
        r = client.post("/api/v1/auth/login", json={"email": email, "password": password})
        data = r.json()["data"]
        return data["access_token"], data["refresh_token"]

    return _do


@pytest.fixture()
def owner_token(client, db_session):
    """Creates an OWNER user directly via the DB session and returns a logged-in access token."""
    from auth.hashing import hash_password
    from models.user import User

    role = db_session.query(Role).filter(Role.name == RoleName.OWNER.value).first()
    owner = User(
        full_name="Test Owner",
        email="test.owner@example.com",
        hashed_password=hash_password("OwnerPass1"),
        role_id=role.id,
        is_active=True,
    )
    db_session.add(owner)
    db_session.commit()

    r = client.post("/api/v1/auth/login", json={"email": "test.owner@example.com", "password": "OwnerPass1"})
    return r.json()["data"]["access_token"]


@pytest.fixture()
def staff_token_factory(client, db_session):
    """Returns a function that creates a user with the given role and returns their access token."""
    from auth.hashing import hash_password
    from models.user import User

    def _make(role_name: str, email: str):
        role = db_session.query(Role).filter(Role.name == role_name).first()
        user = User(
            full_name=f"Test {role_name.title()}",
            email=email,
            hashed_password=hash_password("StaffPass1"),
            role_id=role.id,
            is_active=True,
        )
        db_session.add(user)
        db_session.commit()
        r = client.post("/api/v1/auth/login", json={"email": email, "password": "StaffPass1"})
        return r.json()["data"]["access_token"]

    return _make


@pytest.fixture()
def catalog(db_session):
    """Seeds one floor, one room type, two amenities, and returns their IDs for use in room tests."""
    from models.amenity import Amenity
    from models.floor import Floor
    from models.room_type import RoomType

    floor = Floor(name="Floor 1", floor_number=1)
    room_type = RoomType(name="Standard", base_price=1800, max_occupancy=2)
    wifi = Amenity(name="WiFi", icon="wifi")
    ac = Amenity(name="AC", icon="ac")
    db_session.add_all([floor, room_type, wifi, ac])
    db_session.commit()

    return {
        "floor_id": floor.id,
        "room_type_id": room_type.id,
        "wifi_id": wifi.id,
        "ac_id": ac.id,
    }


@pytest.fixture()
def sample_room(client, owner_token, catalog):
    """Creates one room directly via the API and returns its full JSON detail."""
    h = {"Authorization": f"Bearer {owner_token}"}
    r = client.post(
        "/api/v1/rooms",
        json={
            "room_number": "101",
            "floor_id": catalog["floor_id"],
            "room_type_id": catalog["room_type_id"],
            "price_per_night": 1800,
            "capacity": 2,
            "description": "Test room",
            "amenity_ids": [],
        },
        headers=h,
    )
    return r.json()["data"]
