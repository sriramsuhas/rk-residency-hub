"""
Business logic for the maintenance workflow: raising a request, reception
assigning staff, staff accepting and completing work, cancellation, and
owner/reception-facing aggregate stats.
"""
from datetime import datetime, timezone

from fastapi import UploadFile
from sqlalchemy.orm import Session

from models.enums import MaintenanceRequestStatus, NotificationType, RoleName
from models.maintenance_request import MaintenanceRequest
from repositories.audit_log_repository import AuditLogRepository
from repositories.maintenance_repository import MaintenanceRequestRepository
from repositories.room_repository import RoomRepository
from repositories.user_repository import UserRepository
from schemas.maintenance_schemas import MaintenanceRequestCreateRequest
from services.notification_service import NotificationService
from utils.email import send_email
from utils.email_templates import (
    maintenance_assigned_email,
    maintenance_completed_email,
    maintenance_created_email,
)
from utils.enum_utils import status_label
from utils.exceptions import NotFoundError, UnauthorizedError, ValidationAppError
from utils.uploads import save_uploaded_image


class MaintenanceService:
    def __init__(self, db: Session):
        self.db = db
        self.requests = MaintenanceRequestRepository(db)
        self.rooms = RoomRepository(db)
        self.users = UserRepository(db)
        self.notifications = NotificationService(db)
        self.audit = AuditLogRepository(db)

    def create_request(
        self, payload: MaintenanceRequestCreateRequest, customer_id: int, image: UploadFile | None
    ) -> MaintenanceRequest:
        room = self.rooms.get_by_id(payload.room_id)
        if room is None or not room.is_active:
            raise NotFoundError("Room not found")

        image_url = save_uploaded_image(image, "maintenance_images") if image is not None else None

        request = MaintenanceRequest(
            customer_id=customer_id,
            room_id=payload.room_id,
            booking_id=payload.booking_id,
            category=payload.category,
            priority=payload.priority,
            description=payload.description,
            image_url=image_url,
            status=MaintenanceRequestStatus.PENDING,
        )
        request = self.requests.create(request)
        self.audit.log(
            action="MAINTENANCE_REQUEST_CREATED",
            user_id=customer_id,
            entity_type="MaintenanceRequest",
            entity_id=request.id,
        )

        request = self.requests.get_by_id(request.id)
        subject, body = maintenance_created_email(
            request.customer.full_name, status_label(request.category), request.room.room_number
        )
        send_email(request.customer.email, subject, body)

        return request

    def get_request(self, request_id: int) -> MaintenanceRequest:
        request = self.requests.get_by_id(request_id)
        if request is None:
            raise NotFoundError("Maintenance request not found")
        return request

    def get_request_for_viewer(self, request_id: int, requester_id: int, requester_role: str) -> MaintenanceRequest:
        request = self.get_request(request_id)
        is_owner = request.customer_id == requester_id
        is_assigned_staff = request.assigned_staff_id == requester_id
        is_staff_role = requester_role in ("RECEPTION", "OWNER")
        if not (is_owner or is_assigned_staff or is_staff_role):
            raise UnauthorizedError("You do not have access to this maintenance request")
        return request

    def list_my_requests(self, customer_id: int, page: int, page_size: int, status_filter: str | None):
        return self.requests.list_for_customer(customer_id, page, page_size, status_filter)

    def list_my_tasks(self, staff_id: int, page: int, page_size: int, status_filter: str | None):
        return self.requests.list_for_staff(staff_id, page, page_size, status_filter)

    def search_requests(self, **kwargs):
        return self.requests.search(**kwargs)

    def assign(self, request_id: int, staff_id: int, priority, actor_id: int) -> MaintenanceRequest:
        request = self.get_request(request_id)
        if request.status not in (MaintenanceRequestStatus.PENDING.value, MaintenanceRequestStatus.ASSIGNED.value):
            raise ValidationAppError(
                f"Can only assign requests that are PENDING or already ASSIGNED (this one is {status_label(request.status)})"
            )

        staff = self.users.get_by_id(staff_id)
        if staff is None or staff.role.name != RoleName.HOUSEKEEPING.value:
            raise ValidationAppError("staff_id must belong to a HOUSEKEEPING user")

        request.assigned_staff_id = staff_id
        request.status = MaintenanceRequestStatus.ASSIGNED
        request.assigned_at = datetime.now(timezone.utc)
        if priority is not None:
            request.priority = priority
        self.requests.update(request)

        self.notifications.notify(
            user_id=staff_id,
            title="New maintenance task assigned",
            message=f"You've been assigned a {status_label(request.category)} request for Room {request.room.room_number}.",
            notification_type=NotificationType.MAINTENANCE,
            related_entity_type="MaintenanceRequest",
            related_entity_id=request.id,
        )

        subject, body = maintenance_assigned_email(
            request.customer.full_name, status_label(request.category), request.room.room_number
        )
        send_email(request.customer.email, subject, body)

        self.audit.log(
            action="MAINTENANCE_REQUEST_ASSIGNED",
            user_id=actor_id,
            entity_type="MaintenanceRequest",
            entity_id=request.id,
            details=f"assigned_to={staff_id}",
        )
        return self.get_request(request_id)

    def start(self, request_id: int, actor_id: int) -> MaintenanceRequest:
        request = self.get_request(request_id)
        if request.assigned_staff_id != actor_id:
            raise UnauthorizedError("Only the assigned staff member can start this task")
        if request.status != MaintenanceRequestStatus.ASSIGNED.value:
            raise ValidationAppError(f"Only ASSIGNED requests can be started (this one is {status_label(request.status)})")

        request.status = MaintenanceRequestStatus.IN_PROGRESS
        request.started_at = datetime.now(timezone.utc)
        self.requests.update(request)

        self.audit.log(
            action="MAINTENANCE_REQUEST_STARTED", user_id=actor_id, entity_type="MaintenanceRequest", entity_id=request.id
        )
        return self.get_request(request_id)

    def complete(
        self, request_id: int, remarks: str | None, image: UploadFile | None, actor_id: int
    ) -> MaintenanceRequest:
        request = self.get_request(request_id)
        if request.assigned_staff_id != actor_id:
            raise UnauthorizedError("Only the assigned staff member can complete this task")
        if request.status != MaintenanceRequestStatus.IN_PROGRESS.value:
            raise ValidationAppError(
                f"Only IN_PROGRESS requests can be completed (this one is {status_label(request.status)})"
            )

        if image is not None:
            request.completion_image_url = save_uploaded_image(image, "maintenance_images")
        request.remarks = remarks
        request.status = MaintenanceRequestStatus.COMPLETED
        request.completed_at = datetime.now(timezone.utc)
        self.requests.update(request)

        self.notifications.notify(
            user_id=request.customer_id,
            title="Maintenance request completed",
            message=f"Your {status_label(request.category)} request for Room {request.room.room_number} has been resolved.",
            notification_type=NotificationType.MAINTENANCE,
            related_entity_type="MaintenanceRequest",
            related_entity_id=request.id,
        )

        subject, body = maintenance_completed_email(
            request.customer.full_name, status_label(request.category), request.room.room_number
        )
        send_email(request.customer.email, subject, body)

        self.audit.log(
            action="MAINTENANCE_REQUEST_COMPLETED",
            user_id=actor_id,
            entity_type="MaintenanceRequest",
            entity_id=request.id,
        )
        return self.get_request(request_id)

    def cancel(self, request_id: int, requester_id: int, requester_role: str, reason: str | None) -> MaintenanceRequest:
        request = self.get_request(request_id)
        is_owner = request.customer_id == requester_id
        is_staff = requester_role in ("RECEPTION", "OWNER")
        if not (is_owner or is_staff):
            raise UnauthorizedError("You do not have access to this maintenance request")

        if request.status not in (MaintenanceRequestStatus.PENDING.value, MaintenanceRequestStatus.ASSIGNED.value):
            raise ValidationAppError(
                f"Only PENDING or ASSIGNED requests can be cancelled (this one is {status_label(request.status)})"
            )

        request.status = MaintenanceRequestStatus.CANCELLED
        request.cancelled_at = datetime.now(timezone.utc)
        self.requests.update(request)

        self.audit.log(
            action="MAINTENANCE_REQUEST_CANCELLED",
            user_id=requester_id,
            entity_type="MaintenanceRequest",
            entity_id=request.id,
            details=reason,
        )
        return self.get_request(request_id)

    def get_stats(self):
        status_counts = self.requests.count_by_status()
        category_rows = self.requests.category_breakdown()
        most_frequent = category_rows[0][0] if category_rows else None
        workload_rows = self.requests.staff_workload()

        return {
            "total_requests": self.requests.count_all(),
            "pending_count": status_counts.get(MaintenanceRequestStatus.PENDING.value, 0),
            "assigned_count": status_counts.get(MaintenanceRequestStatus.ASSIGNED.value, 0),
            "in_progress_count": status_counts.get(MaintenanceRequestStatus.IN_PROGRESS.value, 0),
            "completed_count": status_counts.get(MaintenanceRequestStatus.COMPLETED.value, 0),
            "cancelled_count": status_counts.get(MaintenanceRequestStatus.CANCELLED.value, 0),
            "average_resolution_hours": self.requests.average_resolution_hours(),
            "most_frequent_category": most_frequent,
            "category_breakdown": [{"category": cat, "count": count} for cat, count in category_rows],
            "staff_workload": [
                {"staff_id": sid, "staff_name": name, "active_count": active, "completed_count": completed}
                for sid, name, active, completed in workload_rows
            ],
        }
