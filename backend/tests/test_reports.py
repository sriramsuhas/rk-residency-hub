"""Tests for report generation: RBAC, both formats, and actual content correctness."""
import csv
import io
from datetime import date, timedelta

TODAY = date.today()


def _dates(offset_in, offset_out):
    return (TODAY + timedelta(days=offset_in)).isoformat(), (TODAY + timedelta(days=offset_out)).isoformat()


def _paid_booking(client, headers, room_id):
    check_in, check_out = _dates(0, 2)
    r = client.post(
        "/api/v1/bookings",
        json={"room_id": room_id, "check_in_date": check_in, "check_out_date": check_out, "num_guests": 1},
        headers=headers,
    )
    booking_id = r.json()["data"]["id"]
    client.post(f"/api/v1/bookings/{booking_id}/pay", json={"method": "CARD"}, headers=headers)
    return booking_id


def test_customer_cannot_access_any_report(client, register_and_login):
    access_token, _ = register_and_login()
    h = {"Authorization": f"Bearer {access_token}"}
    for path in ["revenue", "bookings", "maintenance", "occupancy", "customers"]:
        r = client.get(f"/api/v1/reports/{path}", headers=h)
        assert r.status_code == 403, path


def test_reception_can_access_operational_reports_but_not_customers(client, staff_token_factory):
    reception_token = staff_token_factory("RECEPTION", "report.reception@example.com")
    h = {"Authorization": f"Bearer {reception_token}"}
    for path in ["revenue", "bookings", "maintenance", "occupancy"]:
        r = client.get(f"/api/v1/reports/{path}", headers=h)
        assert r.status_code == 200, path
    r = client.get("/api/v1/reports/customers", headers=h)
    assert r.status_code == 403


def test_owner_can_access_all_reports(client, owner_token):
    h = {"Authorization": f"Bearer {owner_token}"}
    for path in ["revenue", "bookings", "maintenance", "occupancy", "customers"]:
        r = client.get(f"/api/v1/reports/{path}", headers=h)
        assert r.status_code == 200, path


def test_revenue_report_csv_content(client, sample_room, register_and_login, owner_token):
    access_token, _ = register_and_login()
    h = {"Authorization": f"Bearer {access_token}"}
    _paid_booking(client, h, sample_room["id"])

    oh = {"Authorization": f"Bearer {owner_token}"}
    r = client.get("/api/v1/reports/revenue", params={"format": "csv"}, headers=oh)
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("text/csv")

    reader = csv.reader(io.StringIO(r.text))
    rows = list(reader)
    assert rows[0] == ["Date", "Booking ID", "Room", "Customer", "Method", "Amount", "Status"]
    assert len(rows) == 2  # header + 1 payment
    assert rows[1][5] == "3600.00"
    assert rows[1][6] == "SUCCESS"


def test_revenue_report_pdf_is_valid_pdf(client, sample_room, register_and_login, owner_token):
    access_token, _ = register_and_login()
    h = {"Authorization": f"Bearer {access_token}"}
    _paid_booking(client, h, sample_room["id"])

    oh = {"Authorization": f"Bearer {owner_token}"}
    r = client.get("/api/v1/reports/revenue", params={"format": "pdf"}, headers=oh)
    assert r.status_code == 200
    assert r.headers["content-type"] == "application/pdf"
    assert r.content[:4] == b"%PDF"


def test_booking_report_reflects_status_filter(client, sample_room, register_and_login, owner_token):
    access_token, _ = register_and_login()
    h = {"Authorization": f"Bearer {access_token}"}
    _paid_booking(client, h, sample_room["id"])  # CONFIRMED

    oh = {"Authorization": f"Bearer {owner_token}"}
    r = client.get("/api/v1/reports/bookings", params={"format": "csv", "status": "CANCELLED"}, headers=oh)
    reader = csv.reader(io.StringIO(r.text))
    rows = list(reader)
    assert len(rows) == 1  # header only, no CANCELLED bookings


def test_maintenance_report_content(client, sample_room, register_and_login, owner_token):
    access_token, _ = register_and_login()
    h = {"Authorization": f"Bearer {access_token}"}
    client.post(
        "/api/v1/maintenance-requests",
        data={"room_id": sample_room["id"], "category": "WATER", "priority": "URGENT", "description": "Pipe burst in the bathroom"},
        headers=h,
    )

    oh = {"Authorization": f"Bearer {owner_token}"}
    r = client.get("/api/v1/reports/maintenance", params={"format": "csv"}, headers=oh)
    reader = csv.reader(io.StringIO(r.text))
    rows = list(reader)
    assert rows[1][2] == "WATER"
    assert rows[1][3] == "URGENT"
    assert rows[1][4] == "PENDING"


def test_occupancy_report_reflects_checked_in_room(client, sample_room, register_and_login, staff_token_factory, owner_token):
    access_token, _ = register_and_login()
    h = {"Authorization": f"Bearer {access_token}"}
    booking_id = _paid_booking(client, h, sample_room["id"])

    reception_token = staff_token_factory("RECEPTION", "occ.report.reception@example.com")
    client.post(f"/api/v1/bookings/{booking_id}/check-in", headers={"Authorization": f"Bearer {reception_token}"})

    oh = {"Authorization": f"Bearer {owner_token}"}
    r = client.get("/api/v1/reports/occupancy", params={"format": "csv"}, headers=oh)
    reader = csv.reader(io.StringIO(r.text))
    rows = list(reader)
    today_row = [row for row in rows if row and row[0] == TODAY.isoformat()]
    assert len(today_row) == 1
    assert today_row[0][1] == "1"  # 1 room occupied
    assert today_row[0][3] == "100.0%"  # only 1 active room in this isolated test DB


def test_customer_report_reflects_spend(client, sample_room, register_and_login, owner_token):
    access_token, _ = register_and_login()
    h = {"Authorization": f"Bearer {access_token}"}
    _paid_booking(client, h, sample_room["id"])

    oh = {"Authorization": f"Bearer {owner_token}"}
    r = client.get("/api/v1/reports/customers", params={"format": "csv"}, headers=oh)
    reader = csv.reader(io.StringIO(r.text))
    rows = list(reader)
    assert rows[0] == ["Customer ID", "Name", "Email", "Phone", "Registered", "Total Bookings", "Total Spent"]
    matching = [row for row in rows if row[1] == "Test Customer"]
    assert len(matching) == 1
    assert matching[0][5] == "1"
    assert matching[0][6] == "3600.00"


def test_report_filename_is_attachment(client, owner_token):
    h = {"Authorization": f"Bearer {owner_token}"}
    r = client.get("/api/v1/reports/revenue", params={"format": "csv"}, headers=h)
    assert "attachment" in r.headers["content-disposition"]
    assert "revenue-report" in r.headers["content-disposition"]
