"""Tests for reviews and the notification system's integration with other modules.

(Wishlist tests were removed along with the wishlist feature itself.)
"""
from datetime import date, timedelta

TODAY = date.today()


def _dates(offset_in, offset_out):
    return (TODAY + timedelta(days=offset_in)).isoformat(), (TODAY + timedelta(days=offset_out)).isoformat()


def _complete_a_stay(client, headers, room_id, owner_headers, staff_token_factory):
    """Books, pays, checks in, and checks out a room — returns the booking_id."""
    check_in, check_out = _dates(0, 2)
    r = client.post(
        "/api/v1/bookings",
        json={"room_id": room_id, "check_in_date": check_in, "check_out_date": check_out, "num_guests": 1},
        headers=headers,
    )
    booking_id = r.json()["data"]["id"]
    client.post(f"/api/v1/bookings/{booking_id}/pay", json={"method": "CARD"}, headers=headers)

    reception_token = staff_token_factory("RECEPTION", "reviews.reception@example.com")
    rh = {"Authorization": f"Bearer {reception_token}"}
    client.post(f"/api/v1/bookings/{booking_id}/check-in", headers=rh)
    client.post(f"/api/v1/bookings/{booking_id}/check-out", headers=rh)
    return booking_id


# --- Reviews ---


def test_can_review_a_checked_out_booking(client, sample_room, register_and_login, owner_token, staff_token_factory):
    access_token, _ = register_and_login()
    h = {"Authorization": f"Bearer {access_token}"}
    booking_id = _complete_a_stay(client, h, sample_room["id"], owner_token, staff_token_factory)

    r = client.post("/api/v1/reviews", json={"booking_id": booking_id, "rating": 5, "comment": "Wonderful stay"}, headers=h)
    assert r.status_code == 201
    assert r.json()["data"]["rating"] == 5


def test_cannot_review_a_booking_that_is_not_checked_out(client, sample_room, register_and_login):
    access_token, _ = register_and_login()
    h = {"Authorization": f"Bearer {access_token}"}
    check_in, check_out = _dates(5, 8)
    r = client.post(
        "/api/v1/bookings",
        json={"room_id": sample_room["id"], "check_in_date": check_in, "check_out_date": check_out, "num_guests": 1},
        headers=h,
    )
    booking_id = r.json()["data"]["id"]

    r2 = client.post("/api/v1/reviews", json={"booking_id": booking_id, "rating": 4}, headers=h)
    assert r2.status_code == 422


def test_cannot_review_the_same_booking_twice(client, sample_room, register_and_login, owner_token, staff_token_factory):
    access_token, _ = register_and_login()
    h = {"Authorization": f"Bearer {access_token}"}
    booking_id = _complete_a_stay(client, h, sample_room["id"], owner_token, staff_token_factory)

    client.post("/api/v1/reviews", json={"booking_id": booking_id, "rating": 5}, headers=h)
    r2 = client.post("/api/v1/reviews", json={"booking_id": booking_id, "rating": 3}, headers=h)
    assert r2.status_code == 409


def test_cannot_review_someone_elses_booking(client, sample_room, register_and_login, owner_token, staff_token_factory):
    access_token, _ = register_and_login(email="stayer@example.com")
    h = {"Authorization": f"Bearer {access_token}"}
    booking_id = _complete_a_stay(client, h, sample_room["id"], owner_token, staff_token_factory)

    other_token, _ = register_and_login(email="impersonator@example.com")
    r = client.post(
        "/api/v1/reviews", json={"booking_id": booking_id, "rating": 1},
        headers={"Authorization": f"Bearer {other_token}"},
    )
    assert r.status_code == 401


def test_room_reviews_endpoint_shows_average_rating(client, sample_room, register_and_login, owner_token, staff_token_factory):
    access_token, _ = register_and_login()
    h = {"Authorization": f"Bearer {access_token}"}
    booking_id = _complete_a_stay(client, h, sample_room["id"], owner_token, staff_token_factory)
    client.post("/api/v1/reviews", json={"booking_id": booking_id, "rating": 4}, headers=h)

    r = client.get(f"/api/v1/rooms/{sample_room['id']}/reviews")
    assert r.status_code == 200
    assert r.json()["data"]["average_rating"] == 4.0
    assert r.json()["data"]["total"] == 1


def test_author_can_edit_own_review(client, sample_room, register_and_login, owner_token, staff_token_factory):
    access_token, _ = register_and_login()
    h = {"Authorization": f"Bearer {access_token}"}
    booking_id = _complete_a_stay(client, h, sample_room["id"], owner_token, staff_token_factory)
    r = client.post("/api/v1/reviews", json={"booking_id": booking_id, "rating": 3}, headers=h)
    review_id = r.json()["data"]["id"]

    r2 = client.put(f"/api/v1/reviews/{review_id}", json={"rating": 5, "comment": "Actually it was great"}, headers=h)
    assert r2.status_code == 200
    assert r2.json()["data"]["rating"] == 5


def test_owner_can_delete_any_review_for_moderation(client, sample_room, register_and_login, owner_token, staff_token_factory):
    access_token, _ = register_and_login()
    h = {"Authorization": f"Bearer {access_token}"}
    booking_id = _complete_a_stay(client, h, sample_room["id"], owner_token, staff_token_factory)
    r = client.post("/api/v1/reviews", json={"booking_id": booking_id, "rating": 1, "comment": "inappropriate content"}, headers=h)
    review_id = r.json()["data"]["id"]

    r2 = client.delete(f"/api/v1/reviews/{review_id}", headers={"Authorization": f"Bearer {owner_token}"})
    assert r2.status_code == 200


def test_other_customer_cannot_delete_someones_review(client, sample_room, register_and_login, owner_token, staff_token_factory):
    access_token, _ = register_and_login()
    h = {"Authorization": f"Bearer {access_token}"}
    booking_id = _complete_a_stay(client, h, sample_room["id"], owner_token, staff_token_factory)
    r = client.post("/api/v1/reviews", json={"booking_id": booking_id, "rating": 2}, headers=h)
    review_id = r.json()["data"]["id"]

    other_token, _ = register_and_login(email="rando@example.com")
    r2 = client.delete(f"/api/v1/reviews/{review_id}", headers={"Authorization": f"Bearer {other_token}"})
    assert r2.status_code == 401


# --- Notifications (integration with booking/payment/maintenance) ---


def test_payment_success_creates_a_notification(client, sample_room, register_and_login):
    access_token, _ = register_and_login()
    h = {"Authorization": f"Bearer {access_token}"}
    check_in, check_out = _dates(5, 8)
    r = client.post(
        "/api/v1/bookings",
        json={"room_id": sample_room["id"], "check_in_date": check_in, "check_out_date": check_out, "num_guests": 1},
        headers=h,
    )
    booking_id = r.json()["data"]["id"]
    client.post(f"/api/v1/bookings/{booking_id}/pay", json={"method": "CARD"}, headers=h)

    r2 = client.get("/api/v1/notifications", headers=h)
    assert r2.status_code == 200
    body = r2.json()["data"]
    assert body["unread_count"] >= 1
    assert any(n["type"] == "BOOKING" for n in body["items"])


def test_maintenance_assignment_notifies_staff(client, sample_room, register_and_login, staff_token_factory, owner_token):
    access_token, _ = register_and_login()
    h = {"Authorization": f"Bearer {access_token}"}
    r = client.post(
        "/api/v1/maintenance-requests",
        data={"room_id": sample_room["id"], "category": "WIFI", "priority": "LOW", "description": "WiFi is slow in the room"},
        headers=h,
    )
    request_id = r.json()["data"]["id"]

    hk_token = staff_token_factory("HOUSEKEEPING", "notif.hk@example.com")
    hk_user = client.get("/api/v1/users/me", headers={"Authorization": f"Bearer {hk_token}"}).json()["data"]
    oh = {"Authorization": f"Bearer {owner_token}"}
    client.patch(f"/api/v1/maintenance-requests/{request_id}/assign", json={"staff_id": hk_user["id"]}, headers=oh)

    r2 = client.get("/api/v1/notifications", headers={"Authorization": f"Bearer {hk_token}"})
    assert r2.status_code == 200
    assert r2.json()["data"]["unread_count"] == 1
    assert r2.json()["data"]["items"][0]["type"] == "MAINTENANCE"


def test_mark_notification_read(client, sample_room, register_and_login):
    access_token, _ = register_and_login()
    h = {"Authorization": f"Bearer {access_token}"}
    check_in, check_out = _dates(5, 8)
    r = client.post(
        "/api/v1/bookings",
        json={"room_id": sample_room["id"], "check_in_date": check_in, "check_out_date": check_out, "num_guests": 1},
        headers=h,
    )
    booking_id = r.json()["data"]["id"]
    client.post(f"/api/v1/bookings/{booking_id}/pay", json={"method": "CARD"}, headers=h)

    notif = client.get("/api/v1/notifications", headers=h).json()["data"]["items"][0]
    r2 = client.patch(f"/api/v1/notifications/{notif['id']}/read", headers=h)
    assert r2.status_code == 200
    assert r2.json()["data"]["is_read"] is True


def test_mark_all_read(client, sample_room, register_and_login):
    access_token, _ = register_and_login()
    h = {"Authorization": f"Bearer {access_token}"}
    check_in, check_out = _dates(5, 8)
    r = client.post(
        "/api/v1/bookings",
        json={"room_id": sample_room["id"], "check_in_date": check_in, "check_out_date": check_out, "num_guests": 1},
        headers=h,
    )
    booking_id = r.json()["data"]["id"]
    client.post(f"/api/v1/bookings/{booking_id}/pay", json={"method": "CARD"}, headers=h)

    r2 = client.patch("/api/v1/notifications/read-all", headers=h)
    assert r2.status_code == 200

    r3 = client.get("/api/v1/notifications", headers=h)
    assert r3.json()["data"]["unread_count"] == 0


def test_cannot_mark_someone_elses_notification_read(client, sample_room, register_and_login):
    access_token, _ = register_and_login()
    h = {"Authorization": f"Bearer {access_token}"}
    check_in, check_out = _dates(5, 8)
    r = client.post(
        "/api/v1/bookings",
        json={"room_id": sample_room["id"], "check_in_date": check_in, "check_out_date": check_out, "num_guests": 1},
        headers=h,
    )
    booking_id = r.json()["data"]["id"]
    client.post(f"/api/v1/bookings/{booking_id}/pay", json={"method": "CARD"}, headers=h)
    notif = client.get("/api/v1/notifications", headers=h).json()["data"]["items"][0]

    other_token, _ = register_and_login(email="other.notif@example.com")
    r2 = client.patch(
        f"/api/v1/notifications/{notif['id']}/read", headers={"Authorization": f"Bearer {other_token}"}
    )
    assert r2.status_code == 401
