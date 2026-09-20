"""Tests for role-based access control and user profile/admin management."""


def test_customer_cannot_list_users(client, register_and_login):
    access_token, _ = register_and_login()
    r = client.get("/api/v1/users", headers={"Authorization": f"Bearer {access_token}"})
    assert r.status_code == 403


def test_owner_can_list_users(client, owner_token, register_and_login):
    register_and_login()
    r = client.get("/api/v1/users", headers={"Authorization": f"Bearer {owner_token}"})
    assert r.status_code == 200
    body = r.json()["data"]
    assert body["total"] >= 2


def test_owner_can_search_users(client, owner_token, register_and_login):
    register_and_login(email="findme@example.com")
    r = client.get(
        "/api/v1/users", params={"search": "findme"}, headers={"Authorization": f"Bearer {owner_token}"}
    )
    assert r.status_code == 200
    items = r.json()["data"]["items"]
    assert any(u["email"] == "findme@example.com" for u in items)


def test_reception_can_list_users(client, staff_token_factory, register_and_login):
    register_and_login()
    reception_token = staff_token_factory("RECEPTION", "reception.lister@example.com")
    r = client.get("/api/v1/users", headers={"Authorization": f"Bearer {reception_token}"})
    assert r.status_code == 200


def test_update_own_profile(client, register_and_login):
    access_token, _ = register_and_login()
    r = client.put(
        "/api/v1/users/me",
        json={"full_name": "Updated Name"},
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert r.status_code == 200
    assert r.json()["data"]["full_name"] == "Updated Name"


def test_owner_can_change_user_role(client, owner_token, register_and_login, db_session):
    register_and_login()
    from models.user import User

    target = db_session.query(User).filter(User.email == "test.customer@example.com").first()

    r = client.patch(
        f"/api/v1/users/{target.id}/role",
        json={"role": "RECEPTION"},
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    assert r.status_code == 200
    assert r.json()["data"]["role"] == "RECEPTION"


def test_customer_cannot_change_role(client, register_and_login):
    access_token, _ = register_and_login()
    r = client.patch(
        "/api/v1/users/1/role",
        json={"role": "OWNER"},
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert r.status_code == 403


def test_owner_can_deactivate_user(client, owner_token, register_and_login, db_session):
    register_and_login()
    from models.user import User

    target = db_session.query(User).filter(User.email == "test.customer@example.com").first()

    r = client.patch(
        f"/api/v1/users/{target.id}/status",
        json={"is_active": False},
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    assert r.status_code == 200
    assert r.json()["data"]["is_active"] is False

    # Deactivated user should no longer be able to log in.
    login = client.post(
        "/api/v1/auth/login", json={"email": "test.customer@example.com", "password": "SecurePass1"}
    )
    assert login.status_code == 401


def test_change_role_for_nonexistent_user_returns_404(client, owner_token):
    r = client.patch(
        "/api/v1/users/99999/role",
        json={"role": "RECEPTION"},
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    assert r.status_code == 404
