"""
Business logic for reviews. A review can only be created for a booking that
belongs to the reviewer and has reached CHECKED_OUT — this ties reviews to
verified stays rather than letting anyone review any room.
"""
from sqlalchemy.orm import Session

from models.enums import BookingStatus
from models.review import Review
from repositories.booking_repository import BookingRepository
from repositories.review_repository import ReviewRepository
from schemas.review_schemas import ReviewCreateRequest, ReviewUpdateRequest
from utils.exceptions import ConflictError, NotFoundError, UnauthorizedError, ValidationAppError


class ReviewService:
    def __init__(self, db: Session):
        self.db = db
        self.reviews = ReviewRepository(db)
        self.bookings = BookingRepository(db)

    def create_review(self, payload: ReviewCreateRequest, customer_id: int) -> Review:
        booking = self.bookings.get_by_id(payload.booking_id)
        if booking is None:
            raise NotFoundError("Booking not found")
        if booking.customer_id != customer_id:
            raise UnauthorizedError("You can only review your own bookings")
        if booking.status != BookingStatus.CHECKED_OUT.value:
            raise ValidationAppError("You can only review a booking after your stay is complete (checked out)")
        if self.reviews.get_by_booking_id(payload.booking_id) is not None:
            raise ConflictError("This booking has already been reviewed")

        review = Review(
            customer_id=customer_id,
            room_id=booking.room_id,
            booking_id=payload.booking_id,
            rating=payload.rating,
            comment=payload.comment,
        )
        review = self.reviews.create(review)
        return self.reviews.get_by_id(review.id)

    def get_review(self, review_id: int) -> Review:
        review = self.reviews.get_by_id(review_id)
        if review is None:
            raise NotFoundError("Review not found")
        return review

    def update_review(self, review_id: int, payload: ReviewUpdateRequest, requester_id: int) -> Review:
        review = self.get_review(review_id)
        if review.customer_id != requester_id:
            raise UnauthorizedError("You can only edit your own review")

        if payload.rating is not None:
            review.rating = payload.rating
        if payload.comment is not None:
            review.comment = payload.comment
        return self.reviews.update(review)

    def delete_review(self, review_id: int, requester_id: int, requester_role: str) -> None:
        review = self.get_review(review_id)
        is_owner = review.customer_id == requester_id
        is_moderator = requester_role == "OWNER"
        if not (is_owner or is_moderator):
            raise UnauthorizedError("You do not have permission to delete this review")
        self.reviews.delete(review)

    def list_for_room(self, room_id: int, page: int, page_size: int):
        return self.reviews.list_for_room(room_id, page, page_size)

    def list_for_customer(self, customer_id: int, page: int, page_size: int):
        return self.reviews.list_for_customer(customer_id, page, page_size)
