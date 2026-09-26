"""Post queries. Filters stay here so services do not assemble SQL."""

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.models import Comment, Like, Post, Tag
from app.models.content import post_tags

SORTS = {
    "published_at": Post.published_at,
    "created_at": Post.created_at,
    "updated_at": Post.updated_at,
    "title": Post.title,
}


class PostRepository:
    def __init__(self, db: Session):
        self.db = db

    def by_id(self, post_id: int) -> Post | None:
        return self.db.get(Post, post_id)

    def by_slug(self, slug: str) -> Post | None:
        return self.db.scalar(select(Post).where(Post.slug == slug))

    def slug_taken(self, slug: str, ignore_id: int | None = None) -> bool:
        stmt = select(Post.id).where(Post.slug == slug)
        if ignore_id is not None:
            stmt = stmt.where(Post.id != ignore_id)
        return self.db.scalar(stmt) is not None

    def add(self, post: Post) -> Post:
        self.db.add(post)
        self.db.flush()
        return post

    def delete(self, post: Post) -> None:
        self.db.delete(post)
        self.db.flush()

    def _filtered(self, stmt, *, q: str | None, tag: str | None, author: str | None, status: str | None, author_id: int | None):
        if status:
            stmt = stmt.where(Post.status == status)
        if author_id is not None:
            stmt = stmt.where(Post.author_id == author_id)
        if q:
            needle = f"%{q.strip()}%"
            stmt = stmt.where(or_(Post.title.ilike(needle), Post.excerpt.ilike(needle)))
        if tag:
            stmt = stmt.where(Post.tags.any(Tag.name == tag.strip().lower()))
        if author:
            from app.models import Blog

            blog_ids = select(Blog.id).where(Blog.slug == author.strip().lower())
            stmt = stmt.where(Post.blog_id.in_(blog_ids))
        return stmt

    def search(
        self,
        *,
        page: int,
        page_size: int,
        q: str | None = None,
        tag: str | None = None,
        author: str | None = None,
        status: str | None = None,
        author_id: int | None = None,
        sort: str = "published_at",
        order: str = "desc",
    ) -> tuple[list[Post], int]:
        filters = dict(q=q, tag=tag, author=author, status=status, author_id=author_id)
        total = self.db.scalar(self._filtered(select(func.count(Post.id)), **filters)) or 0
        column = SORTS.get(sort, Post.published_at)
        ordering = column.desc() if order != "asc" else column.asc()
        if sort == "published_at":
            ordering = column.desc().nulls_last() if order != "asc" else column.asc().nulls_last()
        stmt = self._filtered(select(Post), **filters).order_by(ordering, Post.id.desc())
        stmt = stmt.offset((page - 1) * page_size).limit(page_size)
        posts = list(self.db.scalars(stmt).unique())
        return posts, int(total)

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

    def tag_counts(self) -> list[tuple[str, int]]:
        rows = self.db.execute(
            select(Tag.name, func.count(func.distinct(Post.id)))
            .select_from(Tag)
            .join(post_tags, post_tags.c.tag_id == Tag.id)
            .join(Post, Post.id == post_tags.c.post_id)
            .where(Post.status == "published")
            .group_by(Tag.name)
            .order_by(func.count(func.distinct(Post.id)).desc(), Tag.name.asc())
            .limit(20)
        ).all()
        return [(name, int(count)) for name, count in rows]

    def liked_by(self, post_id: int, user_id: int) -> bool:
        return (
            self.db.scalar(select(Like.id).where(Like.post_id == post_id, Like.user_id == user_id)) is not None
        )

    def for_author(self, author_id: int) -> list[Post]:
        stmt = select(Post).where(Post.author_id == author_id).order_by(Post.updated_at.desc())
        return list(self.db.scalars(stmt).unique())
