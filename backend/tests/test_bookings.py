"""Tests for booking creation, conflicts, cancellation, and the check-in/check-out workflow."""
from datetime import date, timedelta

TODAY = date.today()


def _dates(offset_in, offset_out):
    return (TODAY + timedelta(days=offset_in)).isoformat(), (TODAY + timedelta(days=offset_out)).isoformat()


def _pay(client, headers, booking_id, method="CARD"):
    return client.post(f"/api/v1/bookings/{booking_id}/pay", json={"method": method}, headers=headers)


def test_availability_check_true_when_free(client, sample_room):
    check_in, check_out = _dates(5, 8)
    r = client.get(f"/api/v1/rooms/{sample_room['id']}/availability", params={"check_in": check_in, "check_out": check_out})
    assert r.status_code == 200
    assert r.json()["data"]["available"] is True


def test_customer_can_create_booking(client, sample_room, register_and_login):
    access_token, _ = register_and_login()
    check_in, check_out = _dates(5, 8)
    r = client.post(
        "/api/v1/bookings",
        json={"room_id": sample_room["id"], "check_in_date": check_in, "check_out_date": check_out, "num_guests": 2},
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert r.status_code == 201
    body = r.json()["data"]
    assert body["status"] == "PENDING_PAYMENT"
    assert body["total_amount"] == 1800 * 3  # 3 nights


def test_booking_blocked_when_guests_exceed_capacity(client, sample_room, register_and_login):
    access_token, _ = register_and_login()
    check_in, check_out = _dates(5, 8)
    r = client.post(
        "/api/v1/bookings",
        json={"room_id": sample_room["id"], "check_in_date": check_in, "check_out_date": check_out, "num_guests": 5},
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert r.status_code == 422


def test_booking_blocked_for_past_checkin_date(client, sample_room, register_and_login):
    access_token, _ = register_and_login()
    check_in, check_out = _dates(-3, 2)
    r = client.post(
        "/api/v1/bookings",
        json={"room_id": sample_room["id"], "check_in_date": check_in, "check_out_date": check_out, "num_guests": 1},
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert r.status_code == 422


def test_checkout_before_checkin_rejected_by_schema(client, sample_room, register_and_login):
    access_token, _ = register_and_login()
    check_in, check_out = _dates(5, 3)
    r = client.post(
        "/api/v1/bookings",
        json={"room_id": sample_room["id"], "check_in_date": check_in, "check_out_date": check_out, "num_guests": 1},
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert r.status_code == 422


def test_overlapping_booking_rejected(client, sample_room, register_and_login):
    access_token, _ = register_and_login()
    h = {"Authorization": f"Bearer {access_token}"}
    check_in, check_out = _dates(5, 10)
    r1 = client.post(
        "/api/v1/bookings",
        json={"room_id": sample_room["id"], "check_in_date": check_in, "check_out_date": check_out, "num_guests": 1},
        headers=h,
    )
    assert r1.status_code == 201

    # Overlapping range (6..12) should be rejected
    overlap_in, overlap_out = _dates(6, 12)
    r2 = client.post(
        "/api/v1/bookings",
        json={"room_id": sample_room["id"], "check_in_date": overlap_in, "check_out_date": overlap_out, "num_guests": 1},
        headers=h,
    )
    assert r2.status_code == 422


def test_adjacent_non_overlapping_bookings_allowed(client, sample_room, register_and_login):
    access_token, _ = register_and_login()
    h = {"Authorization": f"Bearer {access_token}"}
    check_in, check_out = _dates(5, 10)
    r1 = client.post(
        "/api/v1/bookings",
        json={"room_id": sample_room["id"], "check_in_date": check_in, "check_out_date": check_out, "num_guests": 1},
        headers=h,
    )
    assert r1.status_code == 201

    # Starts exactly when the first one ends — should be allowed (half-open interval)
    next_in, next_out = _dates(10, 12)
    r2 = client.post(
        "/api/v1/bookings",
        json={"room_id": sample_room["id"], "check_in_date": next_in, "check_out_date": next_out, "num_guests": 1},
        headers=h,
    )
    assert r2.status_code == 201


def test_customer_can_view_own_booking_history(client, sample_room, register_and_login):
    access_token, _ = register_and_login()
    h = {"Authorization": f"Bearer {access_token}"}
    check_in, check_out = _dates(5, 8)
    client.post(
        "/api/v1/bookings",
        json={"room_id": sample_room["id"], "check_in_date": check_in, "check_out_date": check_out, "num_guests": 1},
        headers=h,
    )
    r = client.get("/api/v1/bookings/me", headers=h)
    assert r.status_code == 200
    assert r.json()["data"]["total"] == 1


def test_other_customer_cannot_view_someone_elses_booking(client, sample_room, register_and_login):
    access_token, _ = register_and_login(email="owner.of.booking@example.com")
    h = {"Authorization": f"Bearer {access_token}"}
    check_in, check_out = _dates(5, 8)
    r = client.post(
        "/api/v1/bookings",
        json={"room_id": sample_room["id"], "check_in_date": check_in, "check_out_date": check_out, "num_guests": 1},
        headers=h,
    )
    booking_id = r.json()["data"]["id"]

    other_token, _ = register_and_login(email="snooper@example.com")
    r2 = client.get(f"/api/v1/bookings/{booking_id}", headers={"Authorization": f"Bearer {other_token}"})
    assert r2.status_code == 401


def test_customer_can_cancel_own_confirmed_booking(client, sample_room, register_and_login):
    access_token, _ = register_and_login()
    h = {"Authorization": f"Bearer {access_token}"}
    check_in, check_out = _dates(5, 8)
    r = client.post(
        "/api/v1/bookings",
        json={"room_id": sample_room["id"], "check_in_date": check_in, "check_out_date": check_out, "num_guests": 1},
        headers=h,
    )
    booking_id = r.json()["data"]["id"]

    r2 = client.post(f"/api/v1/bookings/{booking_id}/cancel", json={"reason": "Change of plans"}, headers=h)
    assert r2.status_code == 200
    assert r2.json()["data"]["status"] == "CANCELLED"


def test_cancelling_frees_up_the_dates(client, sample_room, register_and_login):
    access_token, _ = register_and_login()
    h = {"Authorization": f"Bearer {access_token}"}
    check_in, check_out = _dates(5, 8)
    r = client.post(
        "/api/v1/bookings",
        json={"room_id": sample_room["id"], "check_in_date": check_in, "check_out_date": check_out, "num_guests": 1},
        headers=h,
    )
    booking_id = r.json()["data"]["id"]
    client.post(f"/api/v1/bookings/{booking_id}/cancel", json={}, headers=h)

    # Same dates should now be free again
    r2 = client.post(
        "/api/v1/bookings",
        json={"room_id": sample_room["id"], "check_in_date": check_in, "check_out_date": check_out, "num_guests": 1},
        headers=h,
    )
    assert r2.status_code == 201


def test_reception_can_check_in_and_check_out(client, sample_room, register_and_login, staff_token_factory):
    access_token, _ = register_and_login()
    h = {"Authorization": f"Bearer {access_token}"}
    check_in, check_out = _dates(0, 3)
    r = client.post(
        "/api/v1/bookings",
        json={"room_id": sample_room["id"], "check_in_date": check_in, "check_out_date": check_out, "num_guests": 1},
        headers=h,
    )
    booking_id = r.json()["data"]["id"]
    _pay(client, h, booking_id)

    reception_token = staff_token_factory("RECEPTION", "reception@example.com")
    rh = {"Authorization": f"Bearer {reception_token}"}

    r2 = client.post(f"/api/v1/bookings/{booking_id}/check-in", headers=rh)
    assert r2.status_code == 200
    assert r2.json()["data"]["status"] == "CHECKED_IN"

    # Room should now show as BOOKED
    room = client.get(f"/api/v1/rooms/{sample_room['id']}").json()["data"]
    assert room["availability_status"] == "BOOKED"

    r3 = client.post(f"/api/v1/bookings/{booking_id}/check-out", headers=rh)
    assert r3.status_code == 200
    assert r3.json()["data"]["status"] == "CHECKED_OUT"

    room2 = client.get(f"/api/v1/rooms/{sample_room['id']}").json()["data"]
    assert room2["availability_status"] == "AVAILABLE"
    assert room2["cleaning_status"] == "DIRTY"


def test_cannot_check_in_a_cancelled_booking(client, sample_room, register_and_login, staff_token_factory):
    access_token, _ = register_and_login()
    h = {"Authorization": f"Bearer {access_token}"}
    check_in, check_out = _dates(0, 3)
    r = client.post(
        "/api/v1/bookings",
        json={"room_id": sample_room["id"], "check_in_date": check_in, "check_out_date": check_out, "num_guests": 1},
        headers=h,
    )
    booking_id = r.json()["data"]["id"]
    client.post(f"/api/v1/bookings/{booking_id}/cancel", json={}, headers=h)

    reception_token = staff_token_factory("RECEPTION", "reception@example.com")
    r2 = client.post(f"/api/v1/bookings/{booking_id}/check-in", headers={"Authorization": f"Bearer {reception_token}"})
    assert r2.status_code == 422


def test_cannot_cancel_a_checked_in_booking(client, sample_room, register_and_login, staff_token_factory):
    access_token, _ = register_and_login()
    h = {"Authorization": f"Bearer {access_token}"}
    check_in, check_out = _dates(0, 3)
    r = client.post(
        "/api/v1/bookings",
        json={"room_id": sample_room["id"], "check_in_date": check_in, "check_out_date": check_out, "num_guests": 1},
        headers=h,
    )
    booking_id = r.json()["data"]["id"]

    reception_token = staff_token_factory("RECEPTION", "reception@example.com")
    _pay(client, h, booking_id)
    client.post(f"/api/v1/bookings/{booking_id}/check-in", headers={"Authorization": f"Bearer {reception_token}"})

    r2 = client.post(f"/api/v1/bookings/{booking_id}/cancel", json={}, headers=h)
    assert r2.status_code == 422


def test_customer_cannot_list_all_bookings(client, register_and_login):
    access_token, _ = register_and_login()
    r = client.get("/api/v1/bookings", headers={"Authorization": f"Bearer {access_token}"})
    assert r.status_code == 403


def test_reception_can_search_all_bookings(client, sample_room, register_and_login, staff_token_factory):
    access_token, _ = register_and_login()
    h = {"Authorization": f"Bearer {access_token}"}
    check_in, check_out = _dates(5, 8)
    client.post(
        "/api/v1/bookings",
        json={"room_id": sample_room["id"], "check_in_date": check_in, "check_out_date": check_out, "num_guests": 1},
        headers=h,
    )

    reception_token = staff_token_factory("RECEPTION", "reception@example.com")
    r = client.get("/api/v1/bookings", headers={"Authorization": f"Bearer {reception_token}"})
    assert r.status_code == 200
    assert r.json()["data"]["total"] == 1


def test_reception_can_reassign_room(client, sample_room, register_and_login, staff_token_factory, owner_token, catalog):
    access_token, _ = register_and_login()
    h = {"Authorization": f"Bearer {access_token}"}
    check_in, check_out = _dates(5, 8)
    r = client.post(
        "/api/v1/bookings",
        json={"room_id": sample_room["id"], "check_in_date": check_in, "check_out_date": check_out, "num_guests": 1},
        headers=h,
    )
    booking_id = r.json()["data"]["id"]
    _pay(client, h, booking_id)

    # Create a second room to reassign to
    oh = {"Authorization": f"Bearer {owner_token}"}
    r2 = client.post(
        "/api/v1/rooms",
        json={
            "room_number": "102",
            "floor_id": catalog["floor_id"],
            "room_type_id": catalog["room_type_id"],
            "price_per_night": 2200,
            "capacity": 2,
            "amenity_ids": [],
        },
        headers=oh,
    )
    new_room_id = r2.json()["data"]["id"]

    reception_token = staff_token_factory("RECEPTION", "reception@example.com")
    rh = {"Authorization": f"Bearer {reception_token}"}
    r3 = client.patch(f"/api/v1/bookings/{booking_id}/assign-room", json={"room_id": new_room_id}, headers=rh)
    assert r3.status_code == 200
    assert r3.json()["data"]["room"]["id"] == new_room_id
    assert r3.json()["data"]["total_amount"] == 2200 * 3
