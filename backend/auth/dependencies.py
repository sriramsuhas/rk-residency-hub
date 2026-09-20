"""
Reusable FastAPI dependencies for authentication and role-based authorization.

Usage in a route:
    @router.get("/owner-only")
    def handler(user: User = Depends(require_roles(RoleName.OWNER))):
        ...
"""
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from auth.jwt_handler import TokenError, decode_token
from database.session import get_db
from models.enums import RoleName
from models.user import User

bearer_scheme = HTTPBearer(auto_error=True)


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    """Resolve the User row for the bearer access token, or 401."""
    try:
        payload = decode_token(credentials.credentials, expected_type="access")
    except TokenError as exc:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc

    user = db.get(User, int(payload["sub"]))
    if user is None or not user.is_active:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="User not found or inactive")
    return user


def require_roles(*allowed_roles: RoleName):
    """Dependency factory that 403s unless the current user's role is in allowed_roles."""

    def dependency(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role.name not in {r.value for r in allowed_roles}:
            raise HTTPException(
                status.HTTP_403_FORBIDDEN,
                detail=f"Requires one of roles: {[r.value for r in allowed_roles]}",
            )
        return current_user

    return dependency
