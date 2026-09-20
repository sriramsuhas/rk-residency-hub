"""Tests for room CRUD, search/filter/pagination, RBAC on status updates, and image uploads."""
import io


def _create_room(client, owner_token, catalog, room_number="101", price=1800, amenity_ids=None):
    h = {"Authorization": f"Bearer {owner_token}"}
    r = client.post(
        "/api/v1/rooms",
        json={
            "room_number": room_number,
            "floor_id": catalog["floor_id"],
            "room_type_id": catalog["room_type_id"],
            "price_per_night": price,
            "capacity": 2,
            "description": f"Room {room_number}",
            "amenity_ids": amenity_ids or [],
        },
        headers=h,
    )
    return r


def test_owner_can_create_room(client, owner_token, catalog):
    r = _create_room(client, owner_token, catalog)
    assert r.status_code == 201
    assert r.json()["data"]["room_number"] == "101"


def test_duplicate_room_number_returns_409(client, owner_token, catalog):
    _create_room(client, owner_token, catalog, room_number="101")
    r = _create_room(client, owner_token, catalog, room_number="101")
    assert r.status_code == 409


def test_create_room_with_invalid_floor_returns_404(client, owner_token, catalog):
    h = {"Authorization": f"Bearer {owner_token}"}
    r = client.post(
        "/api/v1/rooms",
        json={
            "room_number": "999",
            "floor_id": 99999,
            "room_type_id": catalog["room_type_id"],
            "price_per_night": 1800,
            "capacity": 2,
            "amenity_ids": [],
        },
        headers=h,
    )
    assert r.status_code == 404


def test_public_can_search_rooms_without_auth(client, owner_token, catalog):
    _create_room(client, owner_token, catalog, room_number="101", price=1800)
    _create_room(client, owner_token, catalog, room_number="102", price=3500)

    r = client.get("/api/v1/rooms")
    assert r.status_code == 200
    assert r.json()["data"]["total"] == 2


def test_search_filters_by_price_range(client, owner_token, catalog):
    _create_room(client, owner_token, catalog, room_number="101", price=1800)
    _create_room(client, owner_token, catalog, room_number="102", price=3500)

    r = client.get("/api/v1/rooms", params={"min_price": 3000})
    items = r.json()["data"]["items"]
    assert len(items) == 1
    assert items[0]["room_number"] == "102"


def test_search_filters_by_amenity(client, owner_token, catalog):
    _create_room(client, owner_token, catalog, room_number="101", amenity_ids=[catalog["wifi_id"]])
    _create_room(client, owner_token, catalog, room_number="102", amenity_ids=[])

    r = client.get("/api/v1/rooms", params={"amenity_ids": [catalog["wifi_id"]]})
    items = r.json()["data"]["items"]
    assert len(items) == 1
    assert items[0]["room_number"] == "101"


def test_search_sorts_by_price_desc(client, owner_token, catalog):
    _create_room(client, owner_token, catalog, room_number="101", price=1800)
    _create_room(client, owner_token, catalog, room_number="102", price=3500)

    r = client.get("/api/v1/rooms", params={"sort_by": "price_desc"})
    items = r.json()["data"]["items"]
    assert [it["room_number"] for it in items] == ["102", "101"]


def test_deactivated_room_excluded_from_search(client, owner_token, catalog):
    h = {"Authorization": f"Bearer {owner_token}"}
    r = _create_room(client, owner_token, catalog, room_number="101")
    room_id = r.json()["data"]["id"]
    client.delete(f"/api/v1/rooms/{room_id}", headers=h)

    r2 = client.get("/api/v1/rooms")
    assert r2.json()["data"]["total"] == 0


def test_room_detail_includes_amenities_and_images(client, owner_token, catalog):
    r = _create_room(client, owner_token, catalog, amenity_ids=[catalog["wifi_id"], catalog["ac_id"]])
    room_id = r.json()["data"]["id"]

    r2 = client.get(f"/api/v1/rooms/{room_id}")
    assert r2.status_code == 200
    assert len(r2.json()["data"]["amenities"]) == 2
    assert r2.json()["data"]["images"] == []


def test_reception_can_update_availability(client, owner_token, catalog, staff_token_factory):
    r = _create_room(client, owner_token, catalog)
    room_id = r.json()["data"]["id"]
    reception_token = staff_token_factory("RECEPTION", "reception@example.com")

    r2 = client.patch(
        f"/api/v1/rooms/{room_id}/availability",
        json={"availability_status": "BOOKED"},
        headers={"Authorization": f"Bearer {reception_token}"},
    )
    assert r2.status_code == 200
    assert r2.json()["data"]["availability_status"] == "BOOKED"


def test_customer_cannot_update_availability(client, owner_token, catalog, register_and_login):
    r = _create_room(client, owner_token, catalog)
    room_id = r.json()["data"]["id"]
    access_token, _ = register_and_login()

    r2 = client.patch(
        f"/api/v1/rooms/{room_id}/availability",
        json={"availability_status": "BOOKED"},
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert r2.status_code == 403


def test_housekeeping_can_update_cleaning_status(client, owner_token, catalog, staff_token_factory):
    r = _create_room(client, owner_token, catalog)
    room_id = r.json()["data"]["id"]
    hk_token = staff_token_factory("HOUSEKEEPING", "hk@example.com")

    r2 = client.patch(
        f"/api/v1/rooms/{room_id}/cleaning-status",
        json={"cleaning_status": "DIRTY"},
        headers={"Authorization": f"Bearer {hk_token}"},
    )
    assert r2.status_code == 200
    assert r2.json()["data"]["cleaning_status"] == "DIRTY"


def test_owner_can_upload_and_delete_room_image(client, owner_token, catalog, tmp_path, monkeypatch):
    from config import settings as settings_module

    monkeypatch.setattr(settings_module.settings, "upload_dir", str(tmp_path))

    r = _create_room(client, owner_token, catalog)
    room_id = r.json()["data"]["id"]
    h = {"Authorization": f"Bearer {owner_token}"}

    png_bytes = bytes.fromhex(
        "89504e470d0a1a0a0000000d4948445200000001000000010802000000907753de"
        "0000000c4944415478da6360000002000155a5c9f10000000049454e44ae426082"
    )
    files = {"file": ("room.png", io.BytesIO(png_bytes), "image/png")}
    r2 = client.post(f"/api/v1/rooms/{room_id}/images", files=files, params={"is_primary": "true"}, headers=h)
    assert r2.status_code == 200
    images = r2.json()["data"]["images"]
    assert len(images) == 1
    assert images[0]["is_primary"] is True

    image_id = images[0]["id"]
    r3 = client.delete(f"/api/v1/rooms/{room_id}/images/{image_id}", headers=h)
    assert r3.status_code == 200
    assert r3.json()["data"]["images"] == []


def test_set_amenities_replaces_existing_set(client, owner_token, catalog):
    r = _create_room(client, owner_token, catalog, amenity_ids=[catalog["wifi_id"]])
    room_id = r.json()["data"]["id"]
    h = {"Authorization": f"Bearer {owner_token}"}

    r2 = client.patch(f"/api/v1/rooms/{room_id}/amenities", json={"amenity_ids": [catalog["ac_id"]]}, headers=h)
    assert r2.status_code == 200
    names = [a["name"] for a in r2.json()["data"]["amenities"]]
    assert names == ["AC"]
