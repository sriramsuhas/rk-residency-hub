"""Tests for the maintenance request lifecycle: raise, assign, start, complete, cancel, and stats."""
import io


def _submit_request(client, headers, room_id, category="AC", priority="MEDIUM", description="The AC is not cooling at all"):
    r = client.post(
        "/api/v1/maintenance-requests",
        data={"room_id": room_id, "category": category, "priority": priority, "description": description},
        headers=headers,
    )
    return r


def _make_housekeeping(client, owner_headers, staff_token_factory, email="housekeeper@example.com"):
    return staff_token_factory("HOUSEKEEPING", email)


def test_customer_can_raise_request(client, sample_room, register_and_login):
    access_token, _ = register_and_login()
    h = {"Authorization": f"Bearer {access_token}"}
    r = _submit_request(client, h, sample_room["id"])
    assert r.status_code == 201
    body = r.json()["data"]
    assert body["status"] == "PENDING"
    assert body["category"] == "AC"


def test_customer_can_view_own_requests(client, sample_room, register_and_login):
    access_token, _ = register_and_login()
    h = {"Authorization": f"Bearer {access_token}"}
    _submit_request(client, h, sample_room["id"])
    r = client.get("/api/v1/maintenance-requests/me", headers=h)
    assert r.status_code == 200
    assert r.json()["data"]["total"] == 1


def test_customer_cannot_search_all_requests(client, register_and_login):
    access_token, _ = register_and_login()
    r = client.get("/api/v1/maintenance-requests", headers={"Authorization": f"Bearer {access_token}"})
    assert r.status_code == 403


def test_reception_can_search_all_requests(client, sample_room, register_and_login, staff_token_factory):
    access_token, _ = register_and_login()
    h = {"Authorization": f"Bearer {access_token}"}
    _submit_request(client, h, sample_room["id"])

    reception_token = staff_token_factory("RECEPTION", "reception@example.com")
    r = client.get("/api/v1/maintenance-requests", headers={"Authorization": f"Bearer {reception_token}"})
    assert r.status_code == 200
    assert r.json()["data"]["total"] == 1


def test_reception_can_assign_to_housekeeping_staff(client, sample_room, register_and_login, staff_token_factory):
    access_token, _ = register_and_login()
    h = {"Authorization": f"Bearer {access_token}"}
    r = _submit_request(client, h, sample_room["id"])
    request_id = r.json()["data"]["id"]

    hk_token = _make_housekeeping(client, None, staff_token_factory)
    hk_login = client.post("/api/v1/auth/login", json={"email": "housekeeper@example.com", "password": "StaffPass1"})
    hk_user = client.get("/api/v1/users/me", headers={"Authorization": f"Bearer {hk_token}"}).json()["data"]

    reception_token = staff_token_factory("RECEPTION", "reception@example.com")
    rh = {"Authorization": f"Bearer {reception_token}"}
    r2 = client.patch(
        f"/api/v1/maintenance-requests/{request_id}/assign",
        json={"staff_id": hk_user["id"], "priority": "HIGH"},
        headers=rh,
    )
    assert r2.status_code == 200
    assert r2.json()["data"]["status"] == "ASSIGNED"
    assert r2.json()["data"]["priority"] == "HIGH"
    assert r2.json()["data"]["assigned_staff"]["id"] == hk_user["id"]


def test_cannot_assign_to_a_non_housekeeping_user(client, sample_room, register_and_login, staff_token_factory, owner_token):
    access_token, _ = register_and_login()
    h = {"Authorization": f"Bearer {access_token}"}
    r = _submit_request(client, h, sample_room["id"])
    request_id = r.json()["data"]["id"]

    # Try assigning to the customer themself (not HOUSEKEEPING)
    customer_me = client.get("/api/v1/users/me", headers=h).json()["data"]
    oh = {"Authorization": f"Bearer {owner_token}"}
    r2 = client.patch(
        f"/api/v1/maintenance-requests/{request_id}/assign",
        json={"staff_id": customer_me["id"]},
        headers=oh,
    )
    assert r2.status_code == 422


def test_assigned_staff_can_start_and_complete(client, sample_room, register_and_login, staff_token_factory, owner_token):
    access_token, _ = register_and_login()
    h = {"Authorization": f"Bearer {access_token}"}
    r = _submit_request(client, h, sample_room["id"])
    request_id = r.json()["data"]["id"]

    hk_token = _make_housekeeping(client, None, staff_token_factory)
    hk_user = client.get("/api/v1/users/me", headers={"Authorization": f"Bearer {hk_token}"}).json()["data"]

    oh = {"Authorization": f"Bearer {owner_token}"}
    client.patch(f"/api/v1/maintenance-requests/{request_id}/assign", json={"staff_id": hk_user["id"]}, headers=oh)

    hkh = {"Authorization": f"Bearer {hk_token}"}
    r2 = client.post(f"/api/v1/maintenance-requests/{request_id}/start", headers=hkh)
    assert r2.status_code == 200
    assert r2.json()["data"]["status"] == "IN_PROGRESS"

    r3 = client.post(
        f"/api/v1/maintenance-requests/{request_id}/complete",
        data={"remarks": "Replaced the AC filter and recharged coolant"},
        headers=hkh,
    )
    assert r3.status_code == 200
    assert r3.json()["data"]["status"] == "COMPLETED"
    assert r3.json()["data"]["remarks"] == "Replaced the AC filter and recharged coolant"


def test_other_staff_cannot_start_someone_elses_task(client, sample_room, register_and_login, staff_token_factory, owner_token):
    access_token, _ = register_and_login()
    h = {"Authorization": f"Bearer {access_token}"}
    r = _submit_request(client, h, sample_room["id"])
    request_id = r.json()["data"]["id"]

    hk_token = _make_housekeeping(client, None, staff_token_factory, email="hk1@example.com")
    hk_user = client.get("/api/v1/users/me", headers={"Authorization": f"Bearer {hk_token}"}).json()["data"]
    oh = {"Authorization": f"Bearer {owner_token}"}
    client.patch(f"/api/v1/maintenance-requests/{request_id}/assign", json={"staff_id": hk_user["id"]}, headers=oh)

    other_hk_token = staff_token_factory("HOUSEKEEPING", "hk2@example.com")
    r2 = client.post(f"/api/v1/maintenance-requests/{request_id}/start", headers={"Authorization": f"Bearer {other_hk_token}"})
    assert r2.status_code == 401


def test_cannot_complete_before_starting(client, sample_room, register_and_login, staff_token_factory, owner_token):
    access_token, _ = register_and_login()
    h = {"Authorization": f"Bearer {access_token}"}
    r = _submit_request(client, h, sample_room["id"])
    request_id = r.json()["data"]["id"]

    hk_token = _make_housekeeping(client, None, staff_token_factory)
    hk_user = client.get("/api/v1/users/me", headers={"Authorization": f"Bearer {hk_token}"}).json()["data"]
    oh = {"Authorization": f"Bearer {owner_token}"}
    client.patch(f"/api/v1/maintenance-requests/{request_id}/assign", json={"staff_id": hk_user["id"]}, headers=oh)

    r2 = client.post(
        f"/api/v1/maintenance-requests/{request_id}/complete",
        data={"remarks": "skip ahead"},
        headers={"Authorization": f"Bearer {hk_token}"},
    )
    assert r2.status_code == 422


def test_customer_can_cancel_pending_request(client, sample_room, register_and_login):
    access_token, _ = register_and_login()
    h = {"Authorization": f"Bearer {access_token}"}
    r = _submit_request(client, h, sample_room["id"])
    request_id = r.json()["data"]["id"]

    r2 = client.post(f"/api/v1/maintenance-requests/{request_id}/cancel", json={"reason": "fixed it myself"}, headers=h)
    assert r2.status_code == 200
    assert r2.json()["data"]["status"] == "CANCELLED"


def test_cannot_cancel_in_progress_request(client, sample_room, register_and_login, staff_token_factory, owner_token):
    access_token, _ = register_and_login()
    h = {"Authorization": f"Bearer {access_token}"}
    r = _submit_request(client, h, sample_room["id"])
    request_id = r.json()["data"]["id"]

    hk_token = _make_housekeeping(client, None, staff_token_factory)
    hk_user = client.get("/api/v1/users/me", headers={"Authorization": f"Bearer {hk_token}"}).json()["data"]
    oh = {"Authorization": f"Bearer {owner_token}"}
    client.patch(f"/api/v1/maintenance-requests/{request_id}/assign", json={"staff_id": hk_user["id"]}, headers=oh)
    client.post(f"/api/v1/maintenance-requests/{request_id}/start", headers={"Authorization": f"Bearer {hk_token}"})

    r2 = client.post(f"/api/v1/maintenance-requests/{request_id}/cancel", json={}, headers=h)
    assert r2.status_code == 422


def test_other_customer_cannot_view_someones_request(client, sample_room, register_and_login):
    access_token, _ = register_and_login(email="requester@example.com")
    h = {"Authorization": f"Bearer {access_token}"}
    r = _submit_request(client, h, sample_room["id"])
    request_id = r.json()["data"]["id"]

    other_token, _ = register_and_login(email="snooper2@example.com")
    r2 = client.get(f"/api/v1/maintenance-requests/{request_id}", headers={"Authorization": f"Bearer {other_token}"})
    assert r2.status_code == 401


def test_housekeeping_sees_own_tasks(client, sample_room, register_and_login, staff_token_factory, owner_token):
    access_token, _ = register_and_login()
    h = {"Authorization": f"Bearer {access_token}"}
    r = _submit_request(client, h, sample_room["id"])
    request_id = r.json()["data"]["id"]

    hk_token = _make_housekeeping(client, None, staff_token_factory)
    hk_user = client.get("/api/v1/users/me", headers={"Authorization": f"Bearer {hk_token}"}).json()["data"]
    oh = {"Authorization": f"Bearer {owner_token}"}
    client.patch(f"/api/v1/maintenance-requests/{request_id}/assign", json={"staff_id": hk_user["id"]}, headers=oh)

    r2 = client.get("/api/v1/maintenance-requests/my-tasks", headers={"Authorization": f"Bearer {hk_token}"})
    assert r2.status_code == 200
    assert r2.json()["data"]["total"] == 1


def test_request_with_image_upload(client, sample_room, register_and_login, tmp_path, monkeypatch):
    from config import settings as settings_module

    monkeypatch.setattr(settings_module.settings, "upload_dir", str(tmp_path))

    access_token, _ = register_and_login()
    h = {"Authorization": f"Bearer {access_token}"}

    png_bytes = bytes.fromhex(
        "89504e470d0a1a0a0000000d4948445200000001000000010802000000907753de"
        "0000000c4944415478da6360000002000155a5c9f10000000049454e44ae426082"
    )
    files = {"image": ("issue.png", io.BytesIO(png_bytes), "image/png")}
    r = client.post(
        "/api/v1/maintenance-requests",
        data={"room_id": sample_room["id"], "category": "BATHROOM", "priority": "URGENT", "description": "Leaking pipe under the sink"},
        files=files,
        headers=h,
    )
    assert r.status_code == 201
    assert r.json()["data"]["image_url"] is not None


def test_stats_endpoint_requires_staff(client, register_and_login):
    access_token, _ = register_and_login()
    r = client.get("/api/v1/maintenance-requests/stats", headers={"Authorization": f"Bearer {access_token}"})
    assert r.status_code == 403


def test_stats_reflects_completed_requests(client, sample_room, register_and_login, staff_token_factory, owner_token):
    access_token, _ = register_and_login()
    h = {"Authorization": f"Bearer {access_token}"}
    r = _submit_request(client, h, sample_room["id"], category="WIFI")
    request_id = r.json()["data"]["id"]

    hk_token = _make_housekeeping(client, None, staff_token_factory)
    hk_user = client.get("/api/v1/users/me", headers={"Authorization": f"Bearer {hk_token}"}).json()["data"]
    oh = {"Authorization": f"Bearer {owner_token}"}
    client.patch(f"/api/v1/maintenance-requests/{request_id}/assign", json={"staff_id": hk_user["id"]}, headers=oh)
    client.post(f"/api/v1/maintenance-requests/{request_id}/start", headers={"Authorization": f"Bearer {hk_token}"})
    client.post(
        f"/api/v1/maintenance-requests/{request_id}/complete",
        data={"remarks": "done"},
        headers={"Authorization": f"Bearer {hk_token}"},
    )

    r2 = client.get("/api/v1/maintenance-requests/stats", headers=oh)
    assert r2.status_code == 200
    stats = r2.json()["data"]
    assert stats["completed_count"] == 1
    assert stats["most_frequent_category"] == "WIFI"
    assert stats["average_resolution_hours"] is not None
    assert len(stats["staff_workload"]) == 1
    assert stats["staff_workload"][0]["completed_count"] == 1
