"""Likes and comments on published posts."""

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.models import Comment, Like, Post, User
from app.schemas import CommentOut, LikeOut


class EngagementService:
    def __init__(self, db: Session):
        self.db = db

    def list_comments(self, post_id: int, viewer: User | None) -> list[CommentOut]:
        post = self._visible(post_id, viewer)
        rows = list(
            self.db.scalars(select(Comment).where(Comment.post_id == post.id).order_by(Comment.created_at.asc()))
        )
        return [self._present(row, viewer) for row in rows]

    def add_comment(self, user: User, post_id: int, body: str) -> CommentOut:
        post = self._published(post_id)
        comment = Comment(post_id=post.id, author_id=user.id, body=body)
        self.db.add(comment)
        self.db.flush()
        return self._present(comment, user)

    def delete_comment(self, user: User, comment_id: int) -> None:
        comment = self.db.get(Comment, comment_id)
        if comment is None:
            raise AppError(404, "not_found", "Comment not found")
        if comment.author_id != user.id:
            raise AppError(403, "forbidden", "You can only delete your own comment")
        self.db.delete(comment)

    def toggle_like(self, user: User, post_id: int) -> LikeOut:
        post = self._published(post_id)
        existing = self.db.scalar(select(Like).where(Like.post_id == post.id, Like.user_id == user.id))
        if existing:
            self.db.delete(existing)
            liked = False
        else:
            self.db.add(Like(post_id=post.id, user_id=user.id))
            liked = True
        self.db.flush()
        count = self.db.scalar(select(func.count()).select_from(Like).where(Like.post_id == post.id)) or 0
        return LikeOut(liked=liked, like_count=int(count))

    def _published(self, post_id: int) -> Post:
        post = self.db.get(Post, post_id)
        if post is None or post.status != "published":
            raise AppError(404, "not_found", "Post not found")
        return post

    def _visible(self, post_id: int, viewer: User | None) -> Post:
        post = self.db.get(Post, post_id)
        if post is None:
            raise AppError(404, "not_found", "Post not found")
        if post.status != "published" and (viewer is None or viewer.id != post.author_id):
            raise AppError(404, "not_found", "Post not found")
        return post

    def _present(self, comment: Comment, viewer: User | None) -> CommentOut:
        return CommentOut(
            id=comment.id,
            body=comment.body,
            created_at=comment.created_at,
            author_id=comment.author_id,
            author_display_name=comment.author.display_name,
            can_delete=bool(viewer and viewer.id == comment.author_id),
        )
