"""Who is calling: optional visitor, or a logged-in user and their blog."""

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.errors import AppError
from app.core.security import decode_access_token
from app.models import Blog, User

bearer = HTTPBearer(auto_error=False)


def _user_from_token(credentials: HTTPAuthorizationCredentials | None, db: Session) -> User | None:
    if credentials is None:
        return None
    user_id = decode_access_token(credentials.credentials)
    user = db.get(User, user_id)
    if user is None:
        raise AppError(401, "unauthorized", "Invalid or expired token")
    return user


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
    db: Session = Depends(get_db),
) -> User:
    user = _user_from_token(credentials, db)
    if user is None:
        raise AppError(401, "unauthorized", "Login required")
    return user


def get_optional_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
    db: Session = Depends(get_db),
) -> User | None:
    return _user_from_token(credentials, db)


def get_tenant_blog(user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> Blog:
    """A user's blog comes from their account, never from the request body."""
    blog = db.scalar(select(Blog).where(Blog.owner_id == user.id))
    if blog is None:
        raise AppError(403, "no_tenant", "This account has no blog")
    return blog
