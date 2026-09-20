"""Direct database access for maintenance requests, including stats aggregation."""
from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from models.enums import MaintenanceRequestStatus
from models.maintenance_request import MaintenanceRequest
from models.user import User


class MaintenanceRequestRepository:
    def __init__(self, db: Session):
        self.db = db

    def _with_relations(self, stmt):
        return stmt.options(
            joinedload(MaintenanceRequest.room),
            joinedload(MaintenanceRequest.customer),
            joinedload(MaintenanceRequest.assigned_staff),
        )

    def get_by_id(self, request_id: int) -> MaintenanceRequest | None:
        stmt = self._with_relations(select(MaintenanceRequest).where(MaintenanceRequest.id == request_id))
        return self.db.execute(stmt).unique().scalar_one_or_none()

    def create(self, request: MaintenanceRequest) -> MaintenanceRequest:
        self.db.add(request)
        self.db.commit()
        self.db.refresh(request)
        return request

    def update(self, request: MaintenanceRequest) -> MaintenanceRequest:
        self.db.commit()
        self.db.refresh(request)
        return request

    def list_for_customer(
        self, customer_id: int, page: int, page_size: int, status_filter: str | None = None
    ) -> tuple[list[MaintenanceRequest], int]:
        stmt = self._with_relations(select(MaintenanceRequest).where(MaintenanceRequest.customer_id == customer_id))
        count_stmt = (
            select(func.count()).select_from(MaintenanceRequest).where(MaintenanceRequest.customer_id == customer_id)
        )
        if status_filter:
            stmt = stmt.where(MaintenanceRequest.status == status_filter)
            count_stmt = count_stmt.where(MaintenanceRequest.status == status_filter)

        total = self.db.execute(count_stmt).scalar_one()
        stmt = stmt.order_by(MaintenanceRequest.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
        items = list(self.db.execute(stmt).unique().scalars().all())
        return items, total

    def list_for_staff(
        self, staff_id: int, page: int, page_size: int, status_filter: str | None = None
    ) -> tuple[list[MaintenanceRequest], int]:
        stmt = self._with_relations(
            select(MaintenanceRequest).where(MaintenanceRequest.assigned_staff_id == staff_id)
        )
        count_stmt = (
            select(func.count())
            .select_from(MaintenanceRequest)
            .where(MaintenanceRequest.assigned_staff_id == staff_id)
        )
        if status_filter:
            stmt = stmt.where(MaintenanceRequest.status == status_filter)
            count_stmt = count_stmt.where(MaintenanceRequest.status == status_filter)

        total = self.db.execute(count_stmt).scalar_one()
        stmt = stmt.order_by(MaintenanceRequest.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
        items = list(self.db.execute(stmt).unique().scalars().all())
        return items, total

    def search(
        self,
        page: int,
        page_size: int,
        status_filter: str | None = None,
        category: str | None = None,
        priority: str | None = None,
        room_id: int | None = None,
        assigned_staff_id: int | None = None,
    ) -> tuple[list[MaintenanceRequest], int]:
        stmt = self._with_relations(select(MaintenanceRequest))
        count_stmt = select(func.count()).select_from(MaintenanceRequest)

        conditions = []
        if status_filter:
            conditions.append(MaintenanceRequest.status == status_filter)
        if category:
            conditions.append(MaintenanceRequest.category == category)
        if priority:
            conditions.append(MaintenanceRequest.priority == priority)
        if room_id:
            conditions.append(MaintenanceRequest.room_id == room_id)
        if assigned_staff_id:
            conditions.append(MaintenanceRequest.assigned_staff_id == assigned_staff_id)

        for condition in conditions:
            stmt = stmt.where(condition)
            count_stmt = count_stmt.where(condition)

        total = self.db.execute(count_stmt).scalar_one()
        stmt = stmt.order_by(MaintenanceRequest.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
        items = list(self.db.execute(stmt).unique().scalars().all())
        return items, total

    # --- Stats aggregation ---

    def count_by_status(self) -> dict[str, int]:
        stmt = select(MaintenanceRequest.status, func.count()).group_by(MaintenanceRequest.status)
        return {status: count for status, count in self.db.execute(stmt).all()}

    def category_breakdown(self) -> list[tuple[str, int]]:
        stmt = (
            select(MaintenanceRequest.category, func.count())
            .group_by(MaintenanceRequest.category)
            .order_by(func.count().desc())
        )
        return list(self.db.execute(stmt).all())

    def average_resolution_hours(self) -> float | None:
        stmt = select(MaintenanceRequest.created_at, MaintenanceRequest.completed_at).where(
            MaintenanceRequest.status == MaintenanceRequestStatus.COMPLETED.value,
            MaintenanceRequest.completed_at.is_not(None),
        )
        rows = self.db.execute(stmt).all()
        if not rows:
            return None
        total_hours = sum((completed - created).total_seconds() / 3600 for created, completed in rows)
        return round(total_hours / len(rows), 2)

    def staff_workload(self) -> list[tuple[int, str, int, int]]:
        """Returns (staff_id, staff_name, active_count, completed_count) for every staff member with assignments."""
        active_statuses = [MaintenanceRequestStatus.ASSIGNED.value, MaintenanceRequestStatus.IN_PROGRESS.value]

        active_stmt = (
            select(MaintenanceRequest.assigned_staff_id, func.count())
            .where(MaintenanceRequest.assigned_staff_id.is_not(None), MaintenanceRequest.status.in_(active_statuses))
            .group_by(MaintenanceRequest.assigned_staff_id)
        )
        completed_stmt = (
            select(MaintenanceRequest.assigned_staff_id, func.count())
            .where(
                MaintenanceRequest.assigned_staff_id.is_not(None),
                MaintenanceRequest.status == MaintenanceRequestStatus.COMPLETED.value,
            )
            .group_by(MaintenanceRequest.assigned_staff_id)
        )
        active_counts = dict(self.db.execute(active_stmt).all())
        completed_counts = dict(self.db.execute(completed_stmt).all())

        staff_ids = set(active_counts) | set(completed_counts)
        if not staff_ids:
            return []

        names_stmt = select(User.id, User.full_name).where(User.id.in_(staff_ids))
        names = dict(self.db.execute(names_stmt).all())

        return [
            (sid, names.get(sid, "Unknown"), active_counts.get(sid, 0), completed_counts.get(sid, 0))
            for sid in staff_ids
        ]

    def count_all(self) -> int:
        return self.db.execute(select(func.count()).select_from(MaintenanceRequest)).scalar_one()
