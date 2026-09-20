"""
JWT creation and verification.

Access tokens carry {sub: user_id, role: role_name, type: "access"}.
Refresh tokens carry {sub: user_id, type: "refresh"} and are additionally
persisted in the refresh_tokens table so they can be revoked server-side.
"""
import secrets
from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt

from config.settings import settings


class TokenError(Exception):
    """Raised when a token is missing, expired, malformed, or the wrong type."""


def _create_token(subject: str, role: str, token_type: str, expires_delta: timedelta) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": subject,
        "role": role,
        "type": token_type,
        "iat": now,
        "exp": now + expires_delta,
        # Ensures two tokens issued within the same second are never byte-identical
        # (JWT has only second-level "iat" precision) — important because refresh
        # tokens are stored under a UNIQUE constraint.
        "jti": secrets.token_urlsafe(16),
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def create_access_token(user_id: int, role: str) -> str:
    return _create_token(
        str(user_id), role, "access", timedelta(minutes=settings.access_token_expire_minutes)
    )


def create_refresh_token(user_id: int, role: str) -> str:
    return _create_token(
        str(user_id), role, "refresh", timedelta(days=settings.refresh_token_expire_days)
    )


def decode_token(token: str, expected_type: str) -> dict:
    """Decode a token and enforce it's the expected type (access vs refresh)."""
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
    except JWTError as exc:
        raise TokenError("Invalid or expired token") from exc

    if payload.get("type") != expected_type:
        raise TokenError(f"Expected a {expected_type} token")
    return payload


def generate_opaque_token() -> str:
    """Random URL-safe token used for password reset links."""
    return secrets.token_urlsafe(32)
