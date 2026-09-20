"""Tests for Owner, Reception, and Housekeeping analytics dashboards."""
from datetime import date, timedelta

TODAY = date.today()


def _dates(offset_in, offset_out):
    return (TODAY + timedelta(days=offset_in)).isoformat(), (TODAY + timedelta(days=offset_out)).isoformat()


def test_owner_dashboard_requires_owner_role(client, register_and_login):
    access_token, _ = register_and_login()
    r = client.get("/api/v1/analytics/owner", headers={"Authorization": f"Bearer {access_token}"})
    assert r.status_code == 403


def test_owner_dashboard_empty_state(client, owner_token):
    r = client.get("/api/v1/analytics/owner", headers={"Authorization": f"Bearer {owner_token}"})
    assert r.status_code == 200
    data = r.json()["data"]
    assert data["total_revenue"] == 0.0
    assert data["occupancy_rate"] == 0.0
    assert data["popular_rooms"] == []


def test_owner_dashboard_reflects_real_booking(client, sample_room, register_and_login, owner_token):
    access_token, _ = register_and_login()
    h = {"Authorization": f"Bearer {access_token}"}
    check_in, check_out = _dates(0, 2)
    r = client.post(
        "/api/v1/bookings",
        json={"room_id": sample_room["id"], "check_in_date": check_in, "check_out_date": check_out, "num_guests": 1},
        headers=h,
    )
    booking_id = r.json()["data"]["id"]
    client.post(f"/api/v1/bookings/{booking_id}/pay", json={"method": "CARD"}, headers=h)

    oh = {"Authorization": f"Bearer {owner_token}"}
    r2 = client.get("/api/v1/analytics/owner", headers=oh)
    data = r2.json()["data"]
    assert data["total_revenue"] == 1800 * 2
    assert data["popular_rooms"][0]["room_number"] == "101"
    assert data["popular_rooms"][0]["booking_count"] == 1


def test_occupancy_rate_reflects_checked_in_room(client, sample_room, register_and_login, owner_token, staff_token_factory):
    access_token, _ = register_and_login()
    h = {"Authorization": f"Bearer {access_token}"}
    check_in, check_out = _dates(0, 2)
    r = client.post(
        "/api/v1/bookings",
        json={"room_id": sample_room["id"], "check_in_date": check_in, "check_out_date": check_out, "num_guests": 1},
        headers=h,
    )
    booking_id = r.json()["data"]["id"]
    client.post(f"/api/v1/bookings/{booking_id}/pay", json={"method": "CARD"}, headers=h)

    reception_token = staff_token_factory("RECEPTION", "occ.reception@example.com")
    client.post(f"/api/v1/bookings/{booking_id}/check-in", headers={"Authorization": f"Bearer {reception_token}"})

    oh = {"Authorization": f"Bearer {owner_token}"}
    r2 = client.get("/api/v1/analytics/owner", headers=oh)
    data = r2.json()["data"]
    assert data["occupied_room_count"] == 1
    assert data["active_room_count"] == 1
    assert data["occupancy_rate"] == 100.0


def test_reception_dashboard_requires_staff_role(client, register_and_login):
    access_token, _ = register_and_login()
    r = client.get("/api/v1/analytics/reception", headers={"Authorization": f"Bearer {access_token}"})
    assert r.status_code == 403


def test_reception_dashboard_counts_todays_checkin(client, sample_room, register_and_login, staff_token_factory):
    access_token, _ = register_and_login()
    h = {"Authorization": f"Bearer {access_token}"}
    check_in, check_out = _dates(0, 2)
    r = client.post(
        "/api/v1/bookings",
        json={"room_id": sample_room["id"], "check_in_date": check_in, "check_out_date": check_out, "num_guests": 1},
        headers=h,
    )
    booking_id = r.json()["data"]["id"]
    client.post(f"/api/v1/bookings/{booking_id}/pay", json={"method": "CARD"}, headers=h)

    reception_token = staff_token_factory("RECEPTION", "dash.reception@example.com")
    rh = {"Authorization": f"Bearer {reception_token}"}
    r2 = client.get("/api/v1/analytics/reception", headers=rh)
    data = r2.json()["data"]
    assert data["todays_expected_checkins"] == 1
    assert data["todays_revenue"] == 1800 * 2


def test_reception_dashboard_counts_pending_bookings(client, sample_room, register_and_login, staff_token_factory):
    access_token, _ = register_and_login()
    h = {"Authorization": f"Bearer {access_token}"}
    check_in, check_out = _dates(5, 8)
    client.post(
        "/api/v1/bookings",
        json={"room_id": sample_room["id"], "check_in_date": check_in, "check_out_date": check_out, "num_guests": 1},
        headers=h,
    )  # never paid — stays PENDING_PAYMENT

    reception_token = staff_token_factory("RECEPTION", "pending.reception@example.com")
    r = client.get("/api/v1/analytics/reception", headers={"Authorization": f"Bearer {reception_token}"})
    assert r.json()["data"]["pending_bookings_count"] == 1


def test_housekeeping_dashboard_requires_staff_role(client, register_and_login):
    access_token, _ = register_and_login()
    r = client.get("/api/v1/analytics/housekeeping", headers={"Authorization": f"Bearer {access_token}"})
    assert r.status_code == 403


def test_housekeeping_dashboard_shows_dirty_rooms_after_checkout(
    client, sample_room, register_and_login, staff_token_factory
):
    access_token, _ = register_and_login()
    h = {"Authorization": f"Bearer {access_token}"}
    check_in, check_out = _dates(0, 2)
    r = client.post(
        "/api/v1/bookings",
        json={"room_id": sample_room["id"], "check_in_date": check_in, "check_out_date": check_out, "num_guests": 1},
        headers=h,
    )
    booking_id = r.json()["data"]["id"]
    client.post(f"/api/v1/bookings/{booking_id}/pay", json={"method": "CARD"}, headers=h)

    reception_token = staff_token_factory("RECEPTION", "hkdash.reception@example.com")
    rh = {"Authorization": f"Bearer {reception_token}"}
    client.post(f"/api/v1/bookings/{booking_id}/check-in", headers=rh)
    client.post(f"/api/v1/bookings/{booking_id}/check-out", headers=rh)

    hk_token = staff_token_factory("HOUSEKEEPING", "hkdash.staff@example.com")
    r2 = client.get("/api/v1/analytics/housekeeping", headers={"Authorization": f"Bearer {hk_token}"})
    data = r2.json()["data"]
    assert data["pending_cleaning_count"] == 1
    assert data["pending_cleaning_rooms"][0]["room_number"] == "101"


def test_housekeeping_dashboard_reflects_pending_maintenance(
    client, sample_room, register_and_login, owner_token, staff_token_factory
):
    access_token, _ = register_and_login()
    h = {"Authorization": f"Bearer {access_token}"}
    client.post(
        "/api/v1/maintenance-requests",
        data={"room_id": sample_room["id"], "category": "AC", "priority": "LOW", "description": "AC filter needs cleaning"},
        headers=h,
    )

    hk_token = staff_token_factory("HOUSEKEEPING", "hkdash2.staff@example.com")
    r = client.get("/api/v1/analytics/housekeeping", headers={"Authorization": f"Bearer {hk_token}"})
    assert r.json()["data"]["pending_maintenance_count"] == 1
