"""Request dependencies: database user, tenant blog, and permission guards."""

from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.errors import AppError
from app.core.permissions import has_permission
from app.core.security import decode_access_token
from app.models import Blog, User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token", auto_error=False)


def _user_from_token(token: str | None, db: Session) -> User | None:
    if not token:
        return None
    user_id = decode_access_token(token)
    user = db.get(User, user_id)
    if user is None or not user.is_active:
        raise AppError(401, "unauthorized", "Invalid or expired token")
    return user


def get_current_user(
    token: str | None = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    user = _user_from_token(token, db)
    if user is None:
        raise AppError(401, "unauthorized", "Login required")
    return user


def get_optional_user(
    token: str | None = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User | None:
    return _user_from_token(token, db)


def get_tenant_blog(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Blog:
    """The caller's blog is the tenant. It is never taken from the request body."""
    blog = db.scalar(select(Blog).where(Blog.owner_id == user.id))
    if blog is None:
        raise AppError(403, "no_tenant", "This account has no blog workspace")
    return blog


def require_permission(permission: str):
    def _guard(user: User = Depends(get_current_user)) -> User:
        if not has_permission(user.role, permission):
            raise AppError(403, "forbidden", "You do not have permission for this action")
        return user

    return _guard
