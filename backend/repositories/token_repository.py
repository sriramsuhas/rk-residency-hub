"""Direct database access for refresh tokens and password reset tokens."""
from sqlalchemy import select
from sqlalchemy.orm import Session

from models.token import PasswordResetToken, RefreshToken


class RefreshTokenRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, token: RefreshToken) -> RefreshToken:
        self.db.add(token)
        self.db.commit()
        self.db.refresh(token)
        return token

    def get_by_token(self, token: str) -> RefreshToken | None:
        stmt = select(RefreshToken).where(RefreshToken.token == token)
        return self.db.execute(stmt).scalar_one_or_none()

    def revoke(self, token_row: RefreshToken) -> None:
        token_row.revoked = True
        self.db.commit()

    def revoke_all_for_user(self, user_id: int) -> None:
        stmt = select(RefreshToken).where(RefreshToken.user_id == user_id, RefreshToken.revoked.is_(False))
        for token_row in self.db.execute(stmt).scalars().all():
            token_row.revoked = True
        self.db.commit()


class PasswordResetTokenRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, token: PasswordResetToken) -> PasswordResetToken:
        self.db.add(token)
        self.db.commit()
        self.db.refresh(token)
        return token

    def get_valid_token(self, token: str) -> PasswordResetToken | None:
        stmt = select(PasswordResetToken).where(
            PasswordResetToken.token == token, PasswordResetToken.used.is_(False)
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def mark_used(self, token_row: PasswordResetToken) -> None:
        token_row.used = True
        self.db.commit()
