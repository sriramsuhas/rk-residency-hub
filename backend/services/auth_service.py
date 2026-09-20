"""
Business logic for authentication: register, login, refresh, logout,
forgot/reset/change password. Routes stay thin and just call into this.
"""
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from auth.hashing import hash_password, verify_password
from auth.jwt_handler import (
    TokenError,
    create_access_token,
    create_refresh_token,
    decode_token,
    generate_opaque_token,
)
from config.settings import settings
from models.enums import RoleName
from models.token import PasswordResetToken, RefreshToken
from models.user import User
from repositories.audit_log_repository import AuditLogRepository
from repositories.token_repository import PasswordResetTokenRepository, RefreshTokenRepository
from repositories.user_repository import RoleRepository, UserRepository
from schemas.auth_schemas import RegisterRequest
from utils.email import send_email
from utils.email_templates import password_reset_email, welcome_email
from utils.exceptions import ConflictError, NotFoundError, UnauthorizedError, ValidationAppError


class AuthService:
    def __init__(self, db: Session):
        self.db = db
        self.users = UserRepository(db)
        self.roles = RoleRepository(db)
        self.refresh_tokens = RefreshTokenRepository(db)
        self.reset_tokens = PasswordResetTokenRepository(db)
        self.audit = AuditLogRepository(db)

    def register(self, payload: RegisterRequest) -> User:
        if self.users.get_by_email(payload.email):
            raise ConflictError("An account with this email already exists")

        customer_role = self.roles.get_by_name(RoleName.CUSTOMER.value)
        if customer_role is None:
            # Should never happen once seed data is loaded; fail loudly rather than silently misassigning.
            raise NotFoundError("CUSTOMER role is not seeded in the database")

        user = User(
            full_name=payload.full_name,
            email=payload.email,
            phone=payload.phone,
            hashed_password=hash_password(payload.password),
            role_id=customer_role.id,
        )
        user = self.users.create(user)
        self.audit.log(action="USER_REGISTERED", user_id=user.id, entity_type="User", entity_id=user.id)

        subject, body = welcome_email(user.full_name)
        send_email(user.email, subject, body)

        return user

    def login(self, email: str, password: str) -> tuple[str, str]:
        user = self.users.get_by_email(email)
        if user is None or not verify_password(password, user.hashed_password):
            raise UnauthorizedError("Incorrect email or password")
        if not user.is_active:
            raise UnauthorizedError("This account has been deactivated")

        access_token = create_access_token(user.id, user.role.name)
        refresh_token_str = create_refresh_token(user.id, user.role.name)

        refresh_row = RefreshToken(
            user_id=user.id,
            token=refresh_token_str,
            expires_at=datetime.now(timezone.utc) + timedelta(days=settings.refresh_token_expire_days),
        )
        self.refresh_tokens.create(refresh_row)
        self.audit.log(action="USER_LOGIN", user_id=user.id, entity_type="User", entity_id=user.id)
        return access_token, refresh_token_str

    def refresh_access_token(self, refresh_token_str: str) -> str:
        try:
            payload = decode_token(refresh_token_str, expected_type="refresh")
        except TokenError as exc:
            raise UnauthorizedError(str(exc)) from exc

        token_row = self.refresh_tokens.get_by_token(refresh_token_str)
        if token_row is None or token_row.revoked:
            raise UnauthorizedError("Refresh token has been revoked")
        if token_row.expires_at.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc):
            raise UnauthorizedError("Refresh token has expired")

        user = self.users.get_by_id(int(payload["sub"]))
        if user is None or not user.is_active:
            raise UnauthorizedError("User not found or inactive")

        return create_access_token(user.id, user.role.name)

    def logout(self, refresh_token_str: str) -> None:
        token_row = self.refresh_tokens.get_by_token(refresh_token_str)
        if token_row is not None and not token_row.revoked:
            self.refresh_tokens.revoke(token_row)
            self.audit.log(action="USER_LOGOUT", user_id=token_row.user_id)

    def forgot_password(self, email: str) -> None:
        user = self.users.get_by_email(email)
        if user is None:
            # Don't reveal whether the email exists — the route responds
            # identically either way, whether or not anything was sent.
            return

        token_str = generate_opaque_token()
        reset_row = PasswordResetToken(
            user_id=user.id,
            token=token_str,
            expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
        )
        self.reset_tokens.create(reset_row)
        self.audit.log(action="PASSWORD_RESET_REQUESTED", user_id=user.id)

        subject, body = password_reset_email(user.full_name, token_str)
        send_email(user.email, subject, body)

    def reset_password(self, token_str: str, new_password: str) -> None:
        token_row = self.reset_tokens.get_valid_token(token_str)
        if token_row is None:
            raise ValidationAppError("Invalid or already-used reset token")
        if token_row.expires_at.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc):
            raise ValidationAppError("Reset token has expired")

        user = self.users.get_by_id(token_row.user_id)
        if user is None:
            raise NotFoundError("User not found")

        user.hashed_password = hash_password(new_password)
        self.users.update(user)
        self.reset_tokens.mark_used(token_row)
        self.refresh_tokens.revoke_all_for_user(user.id)  # force re-login everywhere
        self.audit.log(action="PASSWORD_RESET_COMPLETED", user_id=user.id)

    def change_password(self, user: User, current_password: str, new_password: str) -> None:
        if not verify_password(current_password, user.hashed_password):
            raise UnauthorizedError("Current password is incorrect")
        user.hashed_password = hash_password(new_password)
        self.users.update(user)
        self.refresh_tokens.revoke_all_for_user(user.id)
        self.audit.log(action="PASSWORD_CHANGED", user_id=user.id)
