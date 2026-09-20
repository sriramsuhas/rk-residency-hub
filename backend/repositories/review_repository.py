"""Direct database access for reviews."""
from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from models.review import Review


class ReviewRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, review_id: int) -> Review | None:
        stmt = select(Review).options(joinedload(Review.customer)).where(Review.id == review_id)
        return self.db.execute(stmt).unique().scalar_one_or_none()

    def get_by_booking_id(self, booking_id: int) -> Review | None:
        stmt = select(Review).where(Review.booking_id == booking_id)
        return self.db.execute(stmt).scalar_one_or_none()

    def create(self, review: Review) -> Review:
        self.db.add(review)
        self.db.commit()
        self.db.refresh(review)
        return review

    def update(self, review: Review) -> Review:
        self.db.commit()
        self.db.refresh(review)
        return review

    def delete(self, review: Review) -> None:
        self.db.delete(review)
        self.db.commit()

    def list_for_room(self, room_id: int, page: int, page_size: int) -> tuple[list[Review], int, float | None]:
        stmt = (
            select(Review).options(joinedload(Review.customer)).where(Review.room_id == room_id)
        )
        count_stmt = select(func.count()).select_from(Review).where(Review.room_id == room_id)
        avg_stmt = select(func.avg(Review.rating)).where(Review.room_id == room_id)

        total = self.db.execute(count_stmt).scalar_one()
        avg_rating = self.db.execute(avg_stmt).scalar_one()

        stmt = stmt.order_by(Review.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
        items = list(self.db.execute(stmt).unique().scalars().all())
        return items, total, round(avg_rating, 2) if avg_rating is not None else None

    def list_for_customer(self, customer_id: int, page: int, page_size: int) -> tuple[list[Review], int]:
        stmt = select(Review).options(joinedload(Review.customer)).where(Review.customer_id == customer_id)
        count_stmt = select(func.count()).select_from(Review).where(Review.customer_id == customer_id)

        total = self.db.execute(count_stmt).scalar_one()
        stmt = stmt.order_by(Review.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
        items = list(self.db.execute(stmt).unique().scalars().all())
        return items, total
