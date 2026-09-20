"""Tests for the catalog lookup tables: floors, room types, amenities."""


def test_public_can_list_floors(client, owner_token):
    client.post("/api/v1/floors", json={"name": "Floor 1", "floor_number": 1}, headers={"Authorization": f"Bearer {owner_token}"})
    r = client.get("/api/v1/floors")
    assert r.status_code == 200
    assert len(r.json()["data"]) == 1


def test_unauthenticated_cannot_create_floor(client):
    # No Authorization header at all -> FastAPI's HTTPBearer rejects with 403.
    r = client.post("/api/v1/floors", json={"name": "Floor 1", "floor_number": 1})
    assert r.status_code == 403


def test_customer_cannot_create_floor(client, register_and_login):
    access_token, _ = register_and_login()
    r = client.post(
        "/api/v1/floors",
        json={"name": "Floor 1", "floor_number": 1},
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert r.status_code == 403


def test_owner_can_create_and_update_floor(client, owner_token):
    h = {"Authorization": f"Bearer {owner_token}"}
    r = client.post("/api/v1/floors", json={"name": "Floor 1", "floor_number": 1}, headers=h)
    assert r.status_code == 201
    floor_id = r.json()["data"]["id"]

    r2 = client.put(f"/api/v1/floors/{floor_id}", json={"description": "Updated desc"}, headers=h)
    assert r2.status_code == 200
    assert r2.json()["data"]["description"] == "Updated desc"


def test_duplicate_floor_number_returns_409(client, owner_token):
    h = {"Authorization": f"Bearer {owner_token}"}
    client.post("/api/v1/floors", json={"name": "Floor 1", "floor_number": 1}, headers=h)
    r = client.post("/api/v1/floors", json={"name": "Floor One (dup)", "floor_number": 1}, headers=h)
    assert r.status_code == 409


def test_owner_can_create_room_type(client, owner_token):
    h = {"Authorization": f"Bearer {owner_token}"}
    r = client.post(
        "/api/v1/room-types",
        json={"name": "Deluxe", "base_price": 2800, "max_occupancy": 3},
        headers=h,
    )
    assert r.status_code == 201
    assert r.json()["data"]["base_price"] == 2800


def test_owner_can_create_amenity(client, owner_token):
    h = {"Authorization": f"Bearer {owner_token}"}
    r = client.post("/api/v1/amenities", json={"name": "WiFi", "icon": "wifi"}, headers=h)
    assert r.status_code == 201


def test_owner_cannot_delete_room_type_in_use(client, owner_token, catalog):
    h = {"Authorization": f"Bearer {owner_token}"}
    client.post(
        "/api/v1/rooms",
        json={
            "room_number": "101",
            "floor_id": catalog["floor_id"],
            "room_type_id": catalog["room_type_id"],
            "price_per_night": 1800,
            "capacity": 2,
            "amenity_ids": [],
        },
        headers=h,
    )
    r = client.delete(f"/api/v1/room-types/{catalog['room_type_id']}", headers=h)
    assert r.status_code == 422
