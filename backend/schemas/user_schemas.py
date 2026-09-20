"""Request/response models for user profile and admin user-management endpoints."""
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field, field_validator

from models.enums import RoleName


class UserResponse(BaseModel):
    id: int
    full_name: str
    email: EmailStr
    phone: str | None
    role: RoleName
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}

    @field_validator("role", mode="before")
    @classmethod
    def extract_role_name(cls, value):
        # `value` arrives as the related Role ORM object (has .name); pass strings/enums through.
        return getattr(value, "name", value)


class UpdateProfileRequest(BaseModel):
    full_name: str | None = Field(default=None, min_length=2, max_length=120)
    phone: str | None = Field(default=None, max_length=20)


class UpdateRoleRequest(BaseModel):
    role: RoleName


class UpdateStatusRequest(BaseModel):
    is_active: bool


class PaginatedUsers(BaseModel):
    total: int
    page: int
    page_size: int
    items: list[UserResponse]
