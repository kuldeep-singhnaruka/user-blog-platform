"""Likes and comments. Both require a logged-in user who is not necessarily the author."""

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.cache import invalidate_lists
from app.core.errors import AppError
from app.core.permissions import has_permission
from app.models import Comment, Like, Post, User
from app.schemas import CommentOut, LikeOut
from app.services.audit_service import AuditService


class EngagementService:
    def __init__(self, db: Session):
        self.db = db
        self.audit = AuditService(db)

    def list_comments(self, post_id: int, viewer: User | None) -> list[CommentOut]:
        post = self.db.get(Post, post_id)
        if post is None or post.status != "published":
            if post is None or viewer is None or (viewer.id != post.author_id and not has_permission(viewer.role, "post:moderate")):
                raise AppError(404, "not_found", "Post not found")
        rows = list(
            self.db.scalars(select(Comment).where(Comment.post_id == post_id).order_by(Comment.created_at.asc()))
        )
        return [self._present(row, viewer) for row in rows]

    def add_comment(self, user: User, post_id: int, body: str) -> CommentOut:
        post = self._published(post_id)
        comment = Comment(post_id=post.id, author_id=user.id, body=body)
        self.db.add(comment)
        self.db.flush()
        self.audit.record(
            actor_id=user.id, action="comment.create", resource_type="comment", resource_id=comment.id, detail=str(post.id)
        )
        invalidate_lists()
        return self._present(comment, user)

    def delete_comment(self, user: User, comment_id: int) -> None:
        comment = self.db.get(Comment, comment_id)
        if comment is None:
            raise AppError(404, "not_found", "Comment not found")
        owns = comment.author_id == user.id and has_permission(user.role, "comment:delete_own")
        moderates = has_permission(user.role, "comment:moderate")
        if not owns and not moderates:
            raise AppError(403, "forbidden", "You cannot delete this comment")
        self.db.delete(comment)
        self.audit.record(
            actor_id=user.id, action="comment.delete", resource_type="comment", resource_id=comment_id
        )
        invalidate_lists()

    def toggle_like(self, user: User, post_id: int) -> LikeOut:
        post = self._published(post_id)
        existing = self.db.scalar(select(Like).where(Like.post_id == post.id, Like.user_id == user.id))
        if existing:
            self.db.delete(existing)
            liked = False
            action = "like.remove"
        else:
            self.db.add(Like(post_id=post.id, user_id=user.id))
            liked = True
            action = "like.add"
        self.db.flush()
        self.audit.record(actor_id=user.id, action=action, resource_type="post", resource_id=post.id)
        invalidate_lists()
        count = self.db.scalar(select(func.count()).select_from(Like).where(Like.post_id == post.id)) or 0
        return LikeOut(liked=liked, like_count=int(count))

    def _published(self, post_id: int) -> Post:
        post = self.db.get(Post, post_id)
        if post is None or post.status != "published":
            raise AppError(404, "not_found", "Post not found")
        return post

    def _present(self, comment: Comment, viewer: User | None) -> CommentOut:
        can_delete = False
        if viewer is not None:
            can_delete = viewer.id == comment.author_id or has_permission(viewer.role, "comment:moderate")
        return CommentOut(
            id=comment.id,
            body=comment.body,
            created_at=comment.created_at,
            author_id=comment.author_id,
            author_display_name=comment.author.display_name,
            can_delete=can_delete,
        )
