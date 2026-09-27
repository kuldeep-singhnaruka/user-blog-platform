"""Post queries."""

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.models import Blog, Comment, Like, Post

SORTS = {
    "published_at": Post.published_at,
    "created_at": Post.created_at,
    "title": Post.title,
}


class PostRepository:
    def __init__(self, db: Session):
        self.db = db

    def by_id(self, post_id: int) -> Post | None:
        return self.db.get(Post, post_id)

    def by_slug(self, slug: str) -> Post | None:
        return self.db.scalar(select(Post).where(Post.slug == slug))

    def slug_taken(self, slug: str) -> bool:
        return self.db.scalar(select(Post.id).where(Post.slug == slug)) is not None

    def add(self, post: Post) -> Post:
        self.db.add(post)
        self.db.flush()
        return post

    def delete(self, post: Post) -> None:
        self.db.delete(post)
        self.db.flush()

    def search(
        self,
        *,
        page: int,
        page_size: int,
        q: str | None = None,
        author: str | None = None,
        status: str | None = None,
        author_id: int | None = None,
        sort: str = "published_at",
        order: str = "desc",
    ) -> tuple[list[Post], int]:
        filters = []
        if status:
            filters.append(Post.status == status)
        if author_id is not None:
            filters.append(Post.author_id == author_id)
        if q:
            needle = f"%{q.strip()}%"
            filters.append(or_(Post.title.ilike(needle), Post.excerpt.ilike(needle)))
        if author:
            blog_ids = select(Blog.id).where(Blog.slug == author.strip().lower())
            filters.append(Post.blog_id.in_(blog_ids))

        total = self.db.scalar(select(func.count(Post.id)).where(*filters)) or 0
        column = SORTS.get(sort, Post.published_at)
        ordering = column.asc() if order == "asc" else column.desc()
        stmt = select(Post).where(*filters).order_by(ordering, Post.id.desc())
        stmt = stmt.offset((page - 1) * page_size).limit(page_size)
        return list(self.db.scalars(stmt).unique()), int(total)

    def engagement_counts(self, post_ids: list[int]) -> tuple[dict[int, int], dict[int, int]]:
        if not post_ids:
            return {}, {}
        likes = dict(
            self.db.execute(
                select(Like.post_id, func.count()).where(Like.post_id.in_(post_ids)).group_by(Like.post_id)
            ).all()
        )
        comments = dict(
            self.db.execute(
                select(Comment.post_id, func.count()).where(Comment.post_id.in_(post_ids)).group_by(Comment.post_id)
            ).all()
        )
        return {int(k): int(v) for k, v in likes.items()}, {int(k): int(v) for k, v in comments.items()}

    def liked_by(self, post_id: int, user_id: int) -> bool:
        return self.db.scalar(select(Like.id).where(Like.post_id == post_id, Like.user_id == user_id)) is not None
