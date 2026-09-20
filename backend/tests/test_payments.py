"""Tests for the mock payment gate, invoice generation, and staff refunds."""
import os
from datetime import date, timedelta

TODAY = date.today()


def _dates(offset_in, offset_out):
    return (TODAY + timedelta(days=offset_in)).isoformat(), (TODAY + timedelta(days=offset_out)).isoformat()


def _create_pending_booking(client, headers, room_id, offset_in=5, offset_out=8, guests=1):
    check_in, check_out = _dates(offset_in, offset_out)
    r = client.post(
        "/api/v1/bookings",
        json={"room_id": room_id, "check_in_date": check_in, "check_out_date": check_out, "num_guests": guests},
        headers=headers,
    )
    return r.json()["data"]["id"]


def test_pay_confirms_a_pending_payment_booking(client, sample_room, register_and_login):
    access_token, _ = register_and_login()
    h = {"Authorization": f"Bearer {access_token}"}
    booking_id = _create_pending_booking(client, h, sample_room["id"])

    r = client.post(f"/api/v1/bookings/{booking_id}/pay", json={"method": "CARD"}, headers=h)
    assert r.status_code == 200
    assert r.json()["data"]["status"] == "SUCCESS"
    assert r.json()["data"]["method"] == "CARD"

    booking = client.get(f"/api/v1/bookings/{booking_id}", headers=h).json()["data"]
    assert booking["status"] == "CONFIRMED"


def test_pay_generates_an_invoice(client, sample_room, register_and_login):
    access_token, _ = register_and_login()
    h = {"Authorization": f"Bearer {access_token}"}
    booking_id = _create_pending_booking(client, h, sample_room["id"])
    client.post(f"/api/v1/bookings/{booking_id}/pay", json={"method": "UPI"}, headers=h)

    r = client.get(f"/api/v1/bookings/{booking_id}/invoice", headers=h)
    assert r.status_code == 200
    invoice = r.json()["data"]
    assert invoice["invoice_number"].startswith("INV-")
    assert invoice["subtotal"] == 1800 * 3
    assert round(invoice["tax_amount"], 2) == round(1800 * 3 * 0.12, 2)
    assert round(invoice["total_amount"], 2) == round(invoice["subtotal"] + invoice["tax_amount"], 2)


def test_invoice_pdf_is_downloadable(client, sample_room, register_and_login, tmp_path, monkeypatch):
    from config import settings as settings_module

    monkeypatch.setattr(settings_module.settings, "upload_dir", str(tmp_path))

    access_token, _ = register_and_login()
    h = {"Authorization": f"Bearer {access_token}"}
    booking_id = _create_pending_booking(client, h, sample_room["id"])
    client.post(f"/api/v1/bookings/{booking_id}/pay", json={"method": "CASH"}, headers=h)

    r = client.get(f"/api/v1/bookings/{booking_id}/invoice/pdf", headers=h)
    assert r.status_code == 200
    assert r.headers["content-type"] == "application/pdf"
    assert len(r.content) > 100  # a real PDF, not an empty stub


def test_cannot_pay_twice(client, sample_room, register_and_login):
    access_token, _ = register_and_login()
    h = {"Authorization": f"Bearer {access_token}"}
    booking_id = _create_pending_booking(client, h, sample_room["id"])
    client.post(f"/api/v1/bookings/{booking_id}/pay", json={"method": "CARD"}, headers=h)

    r2 = client.post(f"/api/v1/bookings/{booking_id}/pay", json={"method": "CARD"}, headers=h)
    assert r2.status_code == 422


def test_cannot_pay_for_someone_elses_booking(client, sample_room, register_and_login):
    access_token, _ = register_and_login(email="owner.of.booking@example.com")
    h = {"Authorization": f"Bearer {access_token}"}
    booking_id = _create_pending_booking(client, h, sample_room["id"])

    other_token, _ = register_and_login(email="stranger@example.com")
    r = client.post(
        f"/api/v1/bookings/{booking_id}/pay", json={"method": "CARD"}, headers={"Authorization": f"Bearer {other_token}"}
    )
    assert r.status_code == 401


def test_customer_can_view_own_payment_history(client, sample_room, register_and_login):
    access_token, _ = register_and_login()
    h = {"Authorization": f"Bearer {access_token}"}
    booking_id = _create_pending_booking(client, h, sample_room["id"])
    client.post(f"/api/v1/bookings/{booking_id}/pay", json={"method": "CARD"}, headers=h)

    r = client.get("/api/v1/payments/me", headers=h)
    assert r.status_code == 200
    assert r.json()["data"]["total"] == 1


def test_refund_requires_cancelled_booking(client, sample_room, register_and_login, owner_token):
    access_token, _ = register_and_login()
    h = {"Authorization": f"Bearer {access_token}"}
    booking_id = _create_pending_booking(client, h, sample_room["id"])
    pay_res = client.post(f"/api/v1/bookings/{booking_id}/pay", json={"method": "CARD"}, headers=h)
    payment_id = pay_res.json()["data"]["id"]

    oh = {"Authorization": f"Bearer {owner_token}"}
    r = client.post(f"/api/v1/payments/{payment_id}/refund", json={"reason": "test"}, headers=oh)
    assert r.status_code == 422  # booking is CONFIRMED, not CANCELLED


def test_owner_can_refund_a_cancelled_bookings_payment(client, sample_room, register_and_login, owner_token):
    access_token, _ = register_and_login()
    h = {"Authorization": f"Bearer {access_token}"}
    booking_id = _create_pending_booking(client, h, sample_room["id"])
    pay_res = client.post(f"/api/v1/bookings/{booking_id}/pay", json={"method": "CARD"}, headers=h)
    payment_id = pay_res.json()["data"]["id"]

    # Guests can only cancel while PENDING_PAYMENT/CONFIRMED — this one is CONFIRMED, cancel is allowed.
    client.post(f"/api/v1/bookings/{booking_id}/cancel", json={"reason": "change of plans"}, headers=h)

    oh = {"Authorization": f"Bearer {owner_token}"}
    r = client.post(f"/api/v1/payments/{payment_id}/refund", json={"reason": "guest cancelled"}, headers=oh)
    assert r.status_code == 200
    assert r.json()["data"]["status"] == "REFUNDED"


def test_customer_cannot_refund_payments(client, sample_room, register_and_login):
    access_token, _ = register_and_login()
    h = {"Authorization": f"Bearer {access_token}"}
    booking_id = _create_pending_booking(client, h, sample_room["id"])
    pay_res = client.post(f"/api/v1/bookings/{booking_id}/pay", json={"method": "CARD"}, headers=h)
    payment_id = pay_res.json()["data"]["id"]

    r = client.post(f"/api/v1/payments/{payment_id}/refund", json={}, headers=h)
    assert r.status_code == 403


def test_invoice_not_available_before_payment(client, sample_room, register_and_login):
    access_token, _ = register_and_login()
    h = {"Authorization": f"Bearer {access_token}"}
    booking_id = _create_pending_booking(client, h, sample_room["id"])

    r = client.get(f"/api/v1/bookings/{booking_id}/invoice", headers=h)
    assert r.status_code == 404
