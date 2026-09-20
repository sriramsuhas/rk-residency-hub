"""Business logic for profile self-service and admin (OWNER) user management."""
from sqlalchemy.orm import Session

from models.user import User
from repositories.audit_log_repository import AuditLogRepository
from repositories.user_repository import RoleRepository, UserRepository
from schemas.user_schemas import UpdateProfileRequest
from utils.exceptions import NotFoundError


class UserService:
    def __init__(self, db: Session):
        self.db = db
        self.users = UserRepository(db)
        self.roles = RoleRepository(db)
        self.audit = AuditLogRepository(db)

    def update_profile(self, user: User, payload: UpdateProfileRequest) -> User:
        if payload.full_name is not None:
            user.full_name = payload.full_name
        if payload.phone is not None:
            user.phone = payload.phone
        return self.users.update(user)

    def list_users(self, page: int, page_size: int, search: str | None, role: str | None):
        return self.users.list_paginated(page=page, page_size=page_size, search=search, role=role)

    def change_role(self, target_user_id: int, new_role_name: str, actor: User) -> User:
        target = self.users.get_by_id(target_user_id)
        if target is None:
            raise NotFoundError("User not found")

        role_row = self.roles.get_by_name(new_role_name)
        if role_row is None:
            raise NotFoundError(f"Role '{new_role_name}' does not exist")

        target.role_id = role_row.id
        target = self.users.update(target)
        self.audit.log(
            action="USER_ROLE_CHANGED",
            user_id=actor.id,
            entity_type="User",
            entity_id=target.id,
            details=f"New role: {new_role_name}",
        )
        return target

    def change_status(self, target_user_id: int, is_active: bool, actor: User) -> User:
        target = self.users.get_by_id(target_user_id)
        if target is None:
            raise NotFoundError("User not found")

        target.is_active = is_active
        target = self.users.update(target)
        self.audit.log(
            action="USER_STATUS_CHANGED",
            user_id=actor.id,
            entity_type="User",
            entity_id=target.id,
            details=f"is_active={is_active}",
        )
        return target
