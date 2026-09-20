"""HTTP routes for authentication. Thin — delegates everything to AuthService."""
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from auth.dependencies import get_current_user
from database.session import get_db
from middleware.rate_limiter import auth_rate_limiter
from models.user import User
from schemas.auth_schemas import (
    AccessTokenResponse,
    ChangePasswordRequest,
    ForgotPasswordRequest,
    ForgotPasswordResponse,
    LoginRequest,
    LogoutRequest,
    RefreshRequest,
    RegisterRequest,
    ResetPasswordRequest,
    TokenResponse,
)
from schemas.user_schemas import UserResponse
from services.auth_service import AuthService
from utils.responses import success

router = APIRouter(prefix="/api/v1/auth", tags=["Authentication"])


@router.post("/register", response_model=dict, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest, db: Session = Depends(get_db), _rl: None = Depends(auth_rate_limiter)):
    user = AuthService(db).register(payload)
    return success(UserResponse.model_validate(user).model_dump(), "Registration successful")


@router.post("/login", response_model=dict)
def login(payload: LoginRequest, db: Session = Depends(get_db), _rl: None = Depends(auth_rate_limiter)):
    access_token, refresh_token = AuthService(db).login(payload.email, payload.password)
    tokens = TokenResponse(access_token=access_token, refresh_token=refresh_token)
    return success(tokens.model_dump(), "Login successful")


@router.post("/refresh", response_model=dict)
def refresh(payload: RefreshRequest, db: Session = Depends(get_db)):
    access_token = AuthService(db).refresh_access_token(payload.refresh_token)
    return success(AccessTokenResponse(access_token=access_token).model_dump(), "Token refreshed")


@router.post("/logout", response_model=dict)
def logout(
    payload: LogoutRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    AuthService(db).logout(payload.refresh_token)
    return success(None, "Logged out successfully")


@router.post("/forgot-password", response_model=dict)
def forgot_password(
    payload: ForgotPasswordRequest, db: Session = Depends(get_db), _rl: None = Depends(auth_rate_limiter)
):
    AuthService(db).forgot_password(payload.email)
    # Always the same response whether or not the email exists, and the
    # reset token never appears here — it only ever leaves the backend
    # inside the emailed reset link (see utils/email.py and
    # utils/email_templates.py). If SMTP isn't configured, the email is
    # logged to the console instead of sent (local-dev convenience), but
    # the API response itself never carries the token either way.
    body = ForgotPasswordResponse(message="If that email exists, a reset link has been sent")
    return success(body.model_dump(), body.message)


@router.post("/reset-password", response_model=dict)
def reset_password(payload: ResetPasswordRequest, db: Session = Depends(get_db)):
    AuthService(db).reset_password(payload.token, payload.new_password)
    return success(None, "Password reset successful")


@router.post("/change-password", response_model=dict)
def change_password(
    payload: ChangePasswordRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    AuthService(db).change_password(current_user, payload.current_password, payload.new_password)
    return success(None, "Password changed successfully")
