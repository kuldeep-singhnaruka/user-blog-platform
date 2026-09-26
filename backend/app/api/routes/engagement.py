"""Likes and comments from any logged-in reader."""

from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_optional_user, require_permission
from app.models import User
from app.schemas import CommentIn, CommentOut, LikeOut
from app.services.engagement_service import EngagementService

router = APIRouter(tags=["engagement"])


@router.get("/posts/{post_id}/comments", response_model=list[CommentOut])
def list_comments(
    post_id: int,
    viewer: User | None = Depends(get_optional_user),
    db: Session = Depends(get_db),
) -> list[CommentOut]:
    return EngagementService(db).list_comments(post_id, viewer)


@router.post("/posts/{post_id}/comments", response_model=CommentOut, status_code=201)
def add_comment(
    post_id: int,
    payload: CommentIn,
    user: User = Depends(require_permission("comment:create")),
    db: Session = Depends(get_db),
) -> CommentOut:
    return EngagementService(db).add_comment(user, post_id, payload.body)


@router.delete("/comments/{comment_id}", status_code=204)
def delete_comment(
    comment_id: int,
    user: User = Depends(get_optional_user),
    db: Session = Depends(get_db),
) -> Response:
    from app.core.errors import AppError

    if user is None:
        raise AppError(401, "unauthorized", "Login required")
    EngagementService(db).delete_comment(user, comment_id)
    return Response(status_code=204)


@router.post("/posts/{post_id}/likes", response_model=LikeOut)
def toggle_like(
    post_id: int,
    user: User = Depends(require_permission("like:toggle")),
    db: Session = Depends(get_db),
) -> LikeOut:
    return EngagementService(db).toggle_like(user, post_id)
