"""Tests for the audit log read API — confirms it actually surfaces entries other modules write."""
from datetime import date, timedelta


def test_customer_cannot_view_audit_logs(client, register_and_login):
    access_token, _ = register_and_login()
    r = client.get("/api/v1/audit-logs", headers={"Authorization": f"Bearer {access_token}"})
    assert r.status_code == 403


def test_reception_cannot_view_audit_logs(client, staff_token_factory):
    reception_token = staff_token_factory("RECEPTION", "audit.reception@example.com")
    r = client.get("/api/v1/audit-logs", headers={"Authorization": f"Bearer {reception_token}"})
    assert r.status_code == 403


def test_owner_can_view_audit_logs(client, owner_token, register_and_login):
    register_and_login()  # generates a USER_REGISTERED entry
    r = client.get("/api/v1/audit-logs", headers={"Authorization": f"Bearer {owner_token}"})
    assert r.status_code == 200
    assert r.json()["data"]["total"] >= 1


def test_audit_log_captures_registration_and_login(client, owner_token, register_and_login):
    register_and_login(email="audited.guest@example.com")
    r = client.get(
        "/api/v1/audit-logs", params={"action": "USER_REGISTERED"}, headers={"Authorization": f"Bearer {owner_token}"}
    )
    items = r.json()["data"]["items"]
    assert any(i["action"] == "USER_REGISTERED" for i in items)

    r2 = client.get(
        "/api/v1/audit-logs", params={"action": "USER_LOGIN"}, headers={"Authorization": f"Bearer {owner_token}"}
    )
    items2 = r2.json()["data"]["items"]
    assert any(i["action"] == "USER_LOGIN" for i in items2)


def test_audit_log_captures_booking_and_payment_events(client, sample_room, register_and_login, owner_token):
    access_token, _ = register_and_login()
    h = {"Authorization": f"Bearer {access_token}"}

    check_in = (date.today() + timedelta(days=5)).isoformat()
    check_out = (date.today() + timedelta(days=8)).isoformat()
    r = client.post(
        "/api/v1/bookings",
        json={"room_id": sample_room["id"], "check_in_date": check_in, "check_out_date": check_out, "num_guests": 1},
        headers=h,
    )
    booking_id = r.json()["data"]["id"]
    client.post(f"/api/v1/bookings/{booking_id}/pay", json={"method": "CARD"}, headers=h)

    oh = {"Authorization": f"Bearer {owner_token}"}
    r2 = client.get(
        "/api/v1/audit-logs",
        params={"action": "BOOKING_CREATED", "entity_id": booking_id},
        headers=oh,
    )
    assert any(i["entity_id"] == booking_id for i in r2.json()["data"]["items"])

    r3 = client.get("/api/v1/audit-logs", params={"action": "PAYMENT_SUCCEEDED"}, headers=oh)
    assert r3.json()["data"]["total"] >= 1


def test_audit_log_filter_by_user(client, owner_token, register_and_login):
    access_token, _ = register_and_login(email="specific.user@example.com")
    me = client.get("/api/v1/users/me", headers={"Authorization": f"Bearer {access_token}"}).json()["data"]

    oh = {"Authorization": f"Bearer {owner_token}"}
    r = client.get("/api/v1/audit-logs", params={"user_id": me["id"]}, headers=oh)
    items = r.json()["data"]["items"]
    assert len(items) >= 1
    assert all(i["user"]["id"] == me["id"] for i in items)


def test_audit_log_response_includes_user_summary(client, owner_token, register_and_login):
    register_and_login(email="attributed.user@example.com")
    oh = {"Authorization": f"Bearer {owner_token}"}
    r = client.get("/api/v1/audit-logs", params={"action": "USER_REGISTERED"}, headers=oh)
    item = r.json()["data"]["items"][0]
    assert item["user"]["email"] == "attributed.user@example.com"


def test_audit_log_pagination(client, owner_token, register_and_login):
    for i in range(5):
        register_and_login(email=f"paginated{i}@example.com")

    oh = {"Authorization": f"Bearer {owner_token}"}
    r = client.get("/api/v1/audit-logs", params={"page": 1, "page_size": 3}, headers=oh)
    body = r.json()["data"]
    assert len(body["items"]) == 3
    assert body["total"] >= 10  # 5 registrations + 5 logins
