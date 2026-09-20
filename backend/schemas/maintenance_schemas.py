"""Request/response models for the maintenance workflow."""
from datetime import datetime

from pydantic import BaseModel, Field

from models.enums import MaintenanceCategory, MaintenancePriority, MaintenanceRequestStatus
from schemas.room_schemas import RoomSummaryResponse
from schemas.user_schemas import UserResponse


class MaintenanceRequestCreateRequest(BaseModel):
    room_id: int
    booking_id: int | None = None
    category: MaintenanceCategory
    priority: MaintenancePriority = MaintenancePriority.MEDIUM
    description: str = Field(min_length=5, max_length=1000)


class MaintenanceAssignRequest(BaseModel):
    staff_id: int
    priority: MaintenancePriority | None = None


class MaintenanceCompleteRequest(BaseModel):
    remarks: str | None = Field(default=None, max_length=1000)


class MaintenanceCancelRequest(BaseModel):
    reason: str | None = Field(default=None, max_length=255)


class MaintenanceRequestResponse(BaseModel):
    id: int
    category: MaintenanceCategory
    priority: MaintenancePriority
    description: str
    image_url: str | None
    status: MaintenanceRequestStatus
    assigned_at: datetime | None
    started_at: datetime | None
    completion_image_url: str | None
    remarks: str | None
    completed_at: datetime | None
    cancelled_at: datetime | None
    created_at: datetime
    room: RoomSummaryResponse
    customer: UserResponse
    assigned_staff: UserResponse | None

    model_config = {"from_attributes": True}


class PaginatedMaintenanceRequests(BaseModel):
    total: int
    page: int
    page_size: int
    items: list[MaintenanceRequestResponse]


class CategoryBreakdown(BaseModel):
    category: MaintenanceCategory
    count: int


class StaffWorkload(BaseModel):
    staff_id: int
    staff_name: str
    active_count: int
    completed_count: int


class MaintenanceStatsResponse(BaseModel):
    total_requests: int
    pending_count: int
    assigned_count: int
    in_progress_count: int
    completed_count: int
    cancelled_count: int
    average_resolution_hours: float | None
    most_frequent_category: MaintenanceCategory | None
    category_breakdown: list[CategoryBreakdown]
    staff_workload: list[StaffWorkload]
