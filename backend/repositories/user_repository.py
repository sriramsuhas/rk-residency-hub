"""All direct database access for the User entity lives here. No business logic."""
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from models.role import Role
from models.user import User


class UserRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, user_id: int) -> User | None:
        return self.db.get(User, user_id)

    def get_by_email(self, email: str) -> User | None:
        stmt = select(User).where(func.lower(User.email) == email.lower())
        return self.db.execute(stmt).scalar_one_or_none()

    def create(self, user: User) -> User:
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def update(self, user: User) -> User:
        self.db.commit()
        self.db.refresh(user)
        return user

    def list_paginated(
        self, page: int, page_size: int, search: str | None = None, role: str | None = None
    ) -> tuple[list[User], int]:
        stmt = select(User)
        count_stmt = select(func.count()).select_from(User)

        if search:
            like = f"%{search.lower()}%"
            filter_clause = func.lower(User.full_name).like(like) | func.lower(User.email).like(like)
            stmt = stmt.where(filter_clause)
            count_stmt = count_stmt.where(filter_clause)

        if role:
            stmt = stmt.join(Role).where(Role.name == role)
            count_stmt = count_stmt.join(Role).where(Role.name == role)

        total = self.db.execute(count_stmt).scalar_one()
        stmt = stmt.order_by(User.id).offset((page - 1) * page_size).limit(page_size)
        items = list(self.db.execute(stmt).scalars().all())
        return items, total


class RoleRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_name(self, name: str) -> Role | None:
        stmt = select(Role).where(Role.name == name)
        return self.db.execute(stmt).scalar_one_or_none()

    def get_by_id(self, role_id: int) -> Role | None:
        return self.db.get(Role, role_id)
