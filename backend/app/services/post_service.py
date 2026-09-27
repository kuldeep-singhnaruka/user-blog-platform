"""Create, edit, publish, and list posts. Only the author can change a post."""

from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.models import Blog, Post, User
from app.models.types import utcnow
from app.repositories.posts import PostRepository
from app.schemas import PageMeta, PostDetail, PostListResponse, PostSummary, PostWrite
from app.services.slugs import slugify


class PostService:
    def __init__(self, db: Session):
        self.db = db
        self.posts = PostRepository(db)

    def list_public(self, **filters) -> PostListResponse:
        posts, total = self.posts.search(status="published", **filters)
        return self._page(posts, total, filters["page"], filters["page_size"])

    def list_mine(self, user: User, *, page: int, page_size: int) -> PostListResponse:
        posts, total = self.posts.search(
            page=page,
            page_size=page_size,
            author_id=user.id,
            sort="created_at",
            order="desc",
        )
        return self._page(posts, total, page, page_size)

    def get_public_slug(self, slug: str, viewer: User | None) -> PostDetail:
        post = self.posts.by_slug(slug)
        if post is None or not self._can_view(post, viewer):
            raise AppError(404, "not_found", "Post not found")
        return self._detail(post, viewer)

    def get_manageable(self, post_id: int, viewer: User) -> PostDetail:
        post = self.posts.by_id(post_id)
        if post is None or not self._can_view(post, viewer):
            raise AppError(404, "not_found", "Post not found")
        return self._detail(post, viewer)

    def create(self, user: User, blog: Blog, payload: PostWrite, publish: bool) -> PostDetail:
        post = Post(
            blog_id=blog.id,
            author_id=user.id,
            title=payload.title.strip(),
            slug=self._unique_slug(payload.title),
            excerpt=self._excerpt(payload),
            body=payload.body.strip(),
            status="published" if publish else "draft",
            published_at=utcnow() if publish else None,
            updated_at=utcnow(),
        )
        self.posts.add(post)
        return self._detail(post, user)

    def update(self, user: User, post_id: int, payload: PostWrite) -> PostDetail:
        post = self._owned(post_id, user)
        post.title = payload.title.strip()
        post.excerpt = self._excerpt(payload)
        post.body = payload.body.strip()
        post.updated_at = utcnow()
        self.db.flush()
        return self._detail(post, user)

    def set_published(self, user: User, post_id: int, published: bool) -> PostDetail:
        post = self._owned(post_id, user)
        post.status = "published" if published else "draft"
        if published and post.published_at is None:
            post.published_at = utcnow()
        post.updated_at = utcnow()
        self.db.flush()
        return self._detail(post, user)

    def delete(self, user: User, post_id: int) -> None:
        post = self._owned(post_id, user)
        self.posts.delete(post)

    def _owned(self, post_id: int, user: User) -> Post:
        post = self.posts.by_id(post_id)
        if post is None:
            raise AppError(404, "not_found", "Post not found")
        if post.author_id != user.id:
            raise AppError(403, "forbidden", "You can only change your own posts")
        return post

    def _can_view(self, post: Post, viewer: User | None) -> bool:
        if post.status == "published":
            return True
        return viewer is not None and viewer.id == post.author_id

    def _excerpt(self, payload: PostWrite) -> str:
        if payload.excerpt and payload.excerpt.strip():
            return payload.excerpt.strip()
        return " ".join(payload.body.split())[:180]

    def _unique_slug(self, title: str) -> str:
        base = slugify(title)[:70]
        slug = base
        suffix = 2
        while self.posts.slug_taken(slug):
            slug = f"{base}-{suffix}"
            suffix += 1
        return slug

    def _page(self, posts: list[Post], total: int, page: int, page_size: int) -> PostListResponse:
        likes, comments = self.posts.engagement_counts([post.id for post in posts])
        data = [self._summary(post, likes.get(post.id, 0), comments.get(post.id, 0)) for post in posts]
        return PostListResponse(data=data, meta=PageMeta(page=page, page_size=page_size, total=total))

    def _summary(self, post: Post, like_count: int, comment_count: int) -> PostSummary:
        return PostSummary(
            id=post.id,
            title=post.title,
            slug=post.slug,
            excerpt=post.excerpt,
            status=post.status,
            author_display_name=post.author.display_name,
            author_id=post.author_id,
            blog_slug=post.blog.slug,
            blog_name=post.blog.name,
            like_count=like_count,
            comment_count=comment_count,
            published_at=post.published_at,
            created_at=post.created_at,
        )

    def _detail(self, post: Post, viewer: User | None) -> PostDetail:
        likes, comments = self.posts.engagement_counts([post.id])
        summary = self._summary(post, likes.get(post.id, 0), comments.get(post.id, 0))
        return PostDetail(
            **summary.model_dump(),
            body=post.body,
            liked_by_me=bool(viewer and self.posts.liked_by(post.id, viewer.id)),
            can_edit=bool(viewer and viewer.id == post.author_id),
        )
