"""HTTP routes for reviews."""
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from auth.dependencies import get_current_user, require_roles
from database.session import get_db
from models.enums import RoleName
from models.user import User
from schemas.review_schemas import PaginatedReviews, ReviewCreateRequest, ReviewResponse, ReviewUpdateRequest
from services.review_service import ReviewService
from utils.responses import success

router = APIRouter(prefix="/api/v1/reviews", tags=["Reviews"])


@router.post("", response_model=dict, status_code=status.HTTP_201_CREATED)
def create_review(
    payload: ReviewCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(RoleName.CUSTOMER)),
):
    review = ReviewService(db).create_review(payload, current_user.id)
    return success(ReviewResponse.model_validate(review).model_dump(), "Review submitted")


@router.get("/me", response_model=dict)
def my_reviews(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=50),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(RoleName.CUSTOMER)),
):
    items, total = ReviewService(db).list_for_customer(current_user.id, page, page_size)
    return success(
        {"total": total, "page": page, "page_size": page_size, "items": [ReviewResponse.model_validate(r) for r in items]}
    )


@router.put("/{review_id}", response_model=dict)
def update_review(
    review_id: int,
    payload: ReviewUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    review = ReviewService(db).update_review(review_id, payload, current_user.id)
    return success(ReviewResponse.model_validate(review).model_dump(), "Review updated")


@router.delete("/{review_id}", response_model=dict)
def delete_review(
    review_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    ReviewService(db).delete_review(review_id, current_user.id, current_user.role.name)
    return success(None, "Review deleted")
