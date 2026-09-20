"""Tests for registration, login, tokens, and password flows."""


def test_register_success(client):
    r = client.post(
        "/api/v1/auth/register",
        json={"full_name": "Asha Rao", "email": "asha@example.com", "password": "SecurePass1"},
    )
    assert r.status_code == 201
    body = r.json()
    assert body["success"] is True
    assert body["data"]["role"] == "CUSTOMER"
    assert "hashed_password" not in body["data"]


def test_register_duplicate_email_returns_409(client):
    payload = {"full_name": "Asha Rao", "email": "asha@example.com", "password": "SecurePass1"}
    client.post("/api/v1/auth/register", json=payload)
    r = client.post("/api/v1/auth/register", json=payload)
    assert r.status_code == 409


def test_register_weak_password_rejected(client):
    r = client.post(
        "/api/v1/auth/register",
        json={"full_name": "Asha Rao", "email": "asha2@example.com", "password": "short"},
    )
    assert r.status_code == 422


def test_login_success_returns_tokens(client):
    client.post(
        "/api/v1/auth/register",
        json={"full_name": "Asha Rao", "email": "asha@example.com", "password": "SecurePass1"},
    )
    r = client.post("/api/v1/auth/login", json={"email": "asha@example.com", "password": "SecurePass1"})
    assert r.status_code == 200
    data = r.json()["data"]
    assert "access_token" in data and "refresh_token" in data


def test_login_wrong_password_returns_401(client):
    client.post(
        "/api/v1/auth/register",
        json={"full_name": "Asha Rao", "email": "asha@example.com", "password": "SecurePass1"},
    )
    r = client.post("/api/v1/auth/login", json={"email": "asha@example.com", "password": "WrongPass1"})
    assert r.status_code == 401


def test_login_nonexistent_user_returns_401(client):
    r = client.post("/api/v1/auth/login", json={"email": "ghost@example.com", "password": "whatever1"})
    assert r.status_code == 401


def test_protected_route_without_token_returns_403(client):
    # FastAPI's HTTPBearer(auto_error=True) returns 403 when the
    # Authorization header is missing entirely; our own code returns 401
    # only once a token is present but invalid/expired (tested separately).
    r = client.get("/api/v1/users/me")
    assert r.status_code == 403


def test_protected_route_with_token_returns_profile(client, register_and_login):
    access_token, _ = register_and_login()
    r = client.get("/api/v1/users/me", headers={"Authorization": f"Bearer {access_token}"})
    assert r.status_code == 200
    assert r.json()["data"]["email"] == "test.customer@example.com"


def test_refresh_token_issues_new_access_token(client, register_and_login):
    access_token, refresh_token = register_and_login()
    r = client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})
    assert r.status_code == 200
    assert "access_token" in r.json()["data"]


def test_refresh_with_invalid_token_returns_401(client):
    r = client.post("/api/v1/auth/refresh", json={"refresh_token": "not-a-real-token"})
    assert r.status_code == 401


def test_logout_revokes_refresh_token(client, register_and_login):
    access_token, refresh_token = register_and_login()
    r = client.post(
        "/api/v1/auth/logout",
        json={"refresh_token": refresh_token},
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert r.status_code == 200

    # Using the revoked refresh token again should now fail.
    r2 = client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})
    assert r2.status_code == 401


def test_forgot_and_reset_password_flow(client, register_and_login, db_session):
    register_and_login()

    r = client.post("/api/v1/auth/forgot-password", json={"email": "test.customer@example.com"})
    assert r.status_code == 200
    # The token must never appear in the API response — it only reaches the
    # user via the emailed reset link (or the console log in local dev).
    assert "reset_token" not in r.json()["data"]

    from models.token import PasswordResetToken
    from models.user import User

    user = db_session.query(User).filter(User.email == "test.customer@example.com").first()
    token_row = (
        db_session.query(PasswordResetToken)
        .filter(PasswordResetToken.user_id == user.id)
        .order_by(PasswordResetToken.id.desc())
        .first()
    )
    reset_token = token_row.token

    r2 = client.post(
        "/api/v1/auth/reset-password", json={"token": reset_token, "new_password": "BrandNewPass1"}
    )
    assert r2.status_code == 200

    # Old password no longer works; new one does.
    old_login = client.post(
        "/api/v1/auth/login", json={"email": "test.customer@example.com", "password": "SecurePass1"}
    )
    assert old_login.status_code == 401

    new_login = client.post(
        "/api/v1/auth/login", json={"email": "test.customer@example.com", "password": "BrandNewPass1"}
    )
    assert new_login.status_code == 200


def test_change_password_requires_correct_current_password(client, register_and_login):
    access_token, _ = register_and_login()
    r = client.post(
        "/api/v1/auth/change-password",
        json={"current_password": "WrongCurrent1", "new_password": "AnotherPass1"},
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert r.status_code == 401


def test_change_password_success(client, register_and_login):
    access_token, _ = register_and_login()
    r = client.post(
        "/api/v1/auth/change-password",
        json={"current_password": "SecurePass1", "new_password": "AnotherPass1"},
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert r.status_code == 200

    r2 = client.post(
        "/api/v1/auth/login", json={"email": "test.customer@example.com", "password": "AnotherPass1"}
    )
    assert r2.status_code == 200
