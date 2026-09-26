"""Blog post rules: ownership, publishing, and public search."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.cache import invalidate_lists
from app.core.errors import AppError
from app.core.permissions import has_permission
from app.models import Blog, Post, Tag, User
from app.models.types import utcnow
from app.repositories.posts import PostRepository
from app.schemas import PageMeta, PostDetail, PostListResponse, PostSummary, PostWrite
from app.services.audit_service import AuditService
from app.services.external_service import fetch_topic_summary
from app.services.slugs import slugify


class PostService:
    def __init__(self, db: Session):
        self.db = db
        self.posts = PostRepository(db)
        self.audit = AuditService(db)

    def list_public(self, **filters) -> PostListResponse:
        posts, total = self.posts.search(status="published", **filters)
        return self._page(posts, total, filters["page"], filters["page_size"])

    def list_mine(self, user: User, *, page: int, page_size: int, status: str | None) -> PostListResponse:
        if status and status not in {"draft", "published"}:
            raise AppError(400, "bad_filter", "Status must be draft or published")
        posts, total = self.posts.search(
            page=page,
            page_size=page_size,
            status=status,
            author_id=user.id,
            sort="updated_at",
            order="desc",
        )
        return self._page(posts, total, page, page_size)

    def get_public_slug(self, slug: str, viewer: User | None) -> PostDetail:
        post = self.posts.by_slug(slug)
        if post is None or not self._can_view(post, viewer):
            raise AppError(404, "not_found", "Post not found")
        return self._detail(post, viewer)

    def get_manageable(self, post_id: int, viewer: User) -> PostDetail:
        post = self._visible(post_id, viewer)
        return self._detail(post, viewer)

    def create(self, user: User, blog: Blog, payload: PostWrite, publish: bool) -> PostDetail:
        post = Post(
            blog_id=blog.id,
            author_id=user.id,
            title=payload.title.strip(),
            slug=self._unique_slug(payload.title),
            excerpt=self._excerpt(payload),
            body=payload.body.strip(),
            cover_url=payload.cover_url,
            status="draft",
        )
        self._apply_tags(post, payload.tags)
        self._apply_reference(post, payload.reference_topic)
        if publish:
            post.status = "published"
            post.published_at = utcnow()
        post.updated_at = utcnow()
        self.posts.add(post)
        self.audit.record(
            actor_id=user.id,
            action="post.publish" if publish else "post.create",
            resource_type="post",
            resource_id=post.id,
            detail=post.slug,
        )
        invalidate_lists()
        return self._detail(post, user)

    def update(self, user: User, post_id: int, payload: PostWrite) -> PostDetail:
        post = self._editable(post_id, user)
        post.title = payload.title.strip()
        post.excerpt = self._excerpt(payload)
        post.body = payload.body.strip()
        post.cover_url = payload.cover_url
        self._apply_tags(post, payload.tags)
        if payload.reference_topic != post.reference_topic:
            self._apply_reference(post, payload.reference_topic)
        post.updated_at = utcnow()
        self.db.flush()
        self.audit.record(actor_id=user.id, action="post.update", resource_type="post", resource_id=post.id)
        invalidate_lists()
        return self._detail(post, user)

    def set_published(self, user: User, post_id: int, published: bool) -> PostDetail:
        post = self._editable(post_id, user)
        if published:
            post.status = "published"
            if post.published_at is None:
                post.published_at = utcnow()
            action = "post.publish"
        else:
            if post.author_id != user.id and not has_permission(user.role, "post:moderate"):
                raise AppError(403, "forbidden", "You cannot unpublish this post")
            post.status = "draft"
            action = "post.unpublish"
        post.updated_at = utcnow()
        self.db.flush()
        self.audit.record(actor_id=user.id, action=action, resource_type="post", resource_id=post.id)
        invalidate_lists()
        return self._detail(post, user)

    def delete(self, user: User, post_id: int) -> None:
        post = self.posts.by_id(post_id)
        if post is None:
            raise AppError(404, "not_found", "Post not found")
        owns = post.author_id == user.id and has_permission(user.role, "post:delete_own")
        moderates = has_permission(user.role, "post:moderate")
        if not owns and not moderates:
            raise AppError(403, "forbidden", "You cannot delete this post")
        slug = post.slug
        self.posts.delete(post)
        self.audit.record(
            actor_id=user.id, action="post.delete", resource_type="post", resource_id=post_id, detail=slug
        )
        invalidate_lists()

    def _editable(self, post_id: int, user: User) -> Post:
        post = self.posts.by_id(post_id)
        if post is None:
            raise AppError(404, "not_found", "Post not found")
        if post.author_id == user.id and has_permission(user.role, "post:update_own"):
            return post
        if has_permission(user.role, "post:moderate"):
            return post
        raise AppError(403, "forbidden", "You cannot edit this post")

    def _visible(self, post_id: int, viewer: User) -> Post:
        post = self.posts.by_id(post_id)
        if post is None or not self._can_view(post, viewer):
            raise AppError(404, "not_found", "Post not found")
        return post

    def _can_view(self, post: Post, viewer: User | None) -> bool:
        if post.status == "published":
            return True
        if viewer is None:
            return False
        return viewer.id == post.author_id or has_permission(viewer.role, "post:moderate")

    def _excerpt(self, payload: PostWrite) -> str:
        if payload.excerpt and payload.excerpt.strip():
            return payload.excerpt.strip()
        flat = " ".join(payload.body.split())
        return flat[:180]

    def _unique_slug(self, title: str, ignore_id: int | None = None) -> str:
        base = slugify(title)[:70]
        slug = base
        suffix = 2
        while self.posts.slug_taken(slug, ignore_id=ignore_id):
            slug = f"{base}-{suffix}"
            suffix += 1
        return slug

    def _apply_tags(self, post: Post, names: list[str]) -> None:
        tags: list[Tag] = []
        for name in names:
            tag = self.db.scalar(select(Tag).where(Tag.name == name))
            if tag is None:
                tag = Tag(name=name)
                self.db.add(tag)
                self.db.flush()
            tags.append(tag)
        post.tags = tags

    def _apply_reference(self, post: Post, topic: str | None) -> None:
        post.reference_topic = topic.strip() if topic else None
        post.reference_title = None
        post.reference_extract = None
        post.reference_url = None
        if not post.reference_topic:
            return
        try:
            summary = fetch_topic_summary(post.reference_topic)
        except Exception:
            summary = None
        if not summary:
            return
        post.reference_title = summary.get("title")
        post.reference_extract = summary.get("extract")
        post.reference_url = summary.get("url")

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
            cover_url=post.cover_url,
            tags=[tag.name for tag in post.tags],
            author_display_name=post.author.display_name,
            author_id=post.author_id,
            blog_slug=post.blog.slug,
            blog_name=post.blog.name,
            like_count=like_count,
            comment_count=comment_count,
            published_at=post.published_at,
            created_at=post.created_at,
            updated_at=post.updated_at,
        )

    def _detail(self, post: Post, viewer: User | None) -> PostDetail:
        likes, comments = self.posts.engagement_counts([post.id])
        summary = self._summary(post, likes.get(post.id, 0), comments.get(post.id, 0))
        can_edit = False
        liked = False
        if viewer is not None:
            liked = self.posts.liked_by(post.id, viewer.id)
            can_edit = viewer.id == post.author_id or has_permission(viewer.role, "post:moderate")
        return PostDetail(
            **summary.model_dump(),
            body=post.body,
            reference_topic=post.reference_topic,
            reference_title=post.reference_title,
            reference_extract=post.reference_extract,
            reference_url=post.reference_url,
            liked_by_me=liked,
            can_edit=can_edit,
        )
