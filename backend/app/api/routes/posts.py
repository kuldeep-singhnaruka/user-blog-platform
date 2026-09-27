"""Public reading and the author's own writing."""

from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user, get_optional_user, get_tenant_blog
from app.models import Blog, User
from app.schemas import PostDetail, PostListResponse, PostWrite
from app.services.post_service import PostService

router = APIRouter(tags=["posts"])


@router.get("/posts", response_model=PostListResponse)
def list_posts(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=50),
    q: str | None = Query(None, max_length=100),
    author: str | None = Query(None, max_length=80),
    sort: str = Query("published_at", pattern="^(published_at|created_at|title)$"),
    order: str = Query("desc", pattern="^(asc|desc)$"),
    db: Session = Depends(get_db),
) -> PostListResponse:
    return PostService(db).list_public(
        page=page, page_size=page_size, q=q, author=author, sort=sort, order=order
    )


@router.get("/posts/by-slug/{slug}", response_model=PostDetail)
def post_by_slug(
    slug: str,
    viewer: User | None = Depends(get_optional_user),
    db: Session = Depends(get_db),
) -> PostDetail:
    return PostService(db).get_public_slug(slug, viewer)


@router.get("/me/posts", response_model=PostListResponse)
def my_posts(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=50),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> PostListResponse:
    return PostService(db).list_mine(user, page=page, page_size=page_size)


@router.post("/posts", response_model=PostDetail, status_code=201)
def create_post(
    payload: PostWrite,
    publish: bool = Query(False),
    user: User = Depends(get_current_user),
    blog: Blog = Depends(get_tenant_blog),
    db: Session = Depends(get_db),
) -> PostDetail:
    return PostService(db).create(user, blog, payload, publish)


@router.get("/posts/{post_id}", response_model=PostDetail)
def get_post(
    post_id: int,
    viewer: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> PostDetail:
    return PostService(db).get_manageable(post_id, viewer)


@router.put("/posts/{post_id}", response_model=PostDetail)
def update_post(
    post_id: int,
    payload: PostWrite,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> PostDetail:
    return PostService(db).update(user, post_id, payload)


@router.post("/posts/{post_id}/publish", response_model=PostDetail)
def publish_post(
    post_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> PostDetail:
    return PostService(db).set_published(user, post_id, True)


@router.post("/posts/{post_id}/unpublish", response_model=PostDetail)
def unpublish_post(
    post_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> PostDetail:
    return PostService(db).set_published(user, post_id, False)


@router.delete("/posts/{post_id}", status_code=204)
def delete_post(
    post_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Response:
    PostService(db).delete(user, post_id)
    return Response(status_code=204)
