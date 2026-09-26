"""Create the permission table and, when enabled, a small demo reading room."""

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.permissions import ROLE_PERMISSIONS
from app.core.security import hash_password
from app.models import AuditLog, Blog, Comment, Like, Post, RolePermission, Tag, User
from app.models.types import utcnow
from app.services.slugs import slugify


def seed_database(db: Session) -> None:
    db.execute(delete(RolePermission))
    for role, permissions in ROLE_PERMISSIONS.items():
        for permission in sorted(permissions):
            db.add(RolePermission(role=role, permission=permission))
    db.flush()

    if not settings.seed_demo_data:
        return
    if db.scalar(select(User.id).where(User.email == settings.admin_email.lower())):
        return

    admin, _admin_blog = _account(db, settings.admin_email, settings.admin_password, settings.admin_name, "admin")
    mina, mina_blog = _account(db, "mina@fieldnotes.local", "Author123!", "Mina Rao", "user")
    ravi, _ravi_blog = _account(db, "ravi@fieldnotes.local", "Reader123!", "Ravi Shah", "user")

    first = _post(
        db,
        mina,
        mina_blog,
        "A boundary is a feature",
        "The useful part of a service is the line it refuses to cross.",
        """A production system gets easier to change when each layer has one job.

Routes accept the request. Services decide what is allowed. Repositories talk to the database. Models describe the data. When those lines blur, a small change in the reading room starts breaking the writing desk.

Fieldnotes keeps that split on purpose. The public list never asks who you are. The writing endpoints always do, and they take the blog from the signed-in user rather than from the body of the request.""",
        ["engineering", "architecture"],
        published=True,
    )
    _post(
        db,
        mina,
        mina_blog,
        "Authentication is not authorization",
        "Signing in proves who you are. It does not decide what you may touch.",
        """A token answers a narrow question: which account is calling?

What that account may do lives in a role, and the role is only a bundle of permissions. A reader can like and comment. The author of a post can edit that post. A moderator can take a comment down. An admin can read the audit log.

Least privilege is just this list kept short, then grown only when a real job needs it.""",
        ["auth", "security"],
        published=True,
    )
    _post(
        db,
        mina,
        mina_blog,
        "Make the slow query obvious",
        "Indexes, smaller payloads, and a look at the query plan beat guessing.",
        """The public feed filters on published posts and sorts by the time they went live. That pair of columns is indexed together so the database does not scan every draft to build the homepage.

The list response leaves the full essay out. The detail request is where the body lives. Likes and comment counts are loaded in two grouped queries, not one query per card.

If you are an admin, the query plan endpoint prints the plan for that feed. That is the habit to keep: look at the plan before adding another index.""",
        ["database", "performance"],
        published=True,
    )
    _post(
        db,
        mina,
        mina_blog,
        "Notes from the desk",
        "A draft stays in the author's workspace until it is published.",
        "This draft is visible from Mina's desk and hidden from the public feed.",
        ["drafts"],
        published=False,
    )

    db.add(Comment(post_id=first.id, author_id=ravi.id, body="The tenant note is the part I want to remember."))
    db.add(Like(post_id=first.id, user_id=ravi.id))
    db.add(
        AuditLog(
            actor_id=admin.id,
            action="seed.complete",
            resource_type="system",
            resource_id="demo",
            detail="Demo reading room created",
        )
    )
    db.flush()


def _account(db: Session, email: str, password: str, display_name: str, role: str) -> tuple[User, Blog]:
    user = User(
        email=email.lower(),
        password_hash=hash_password(password),
        display_name=display_name,
        role=role,
    )
    db.add(user)
    db.flush()
    base = slugify(display_name)
    slug = base
    suffix = 2
    while db.scalar(select(Blog.id).where(Blog.slug == slug)):
        slug = f"{base}-{suffix}"
        suffix += 1
    blog = Blog(owner_id=user.id, name=f"{display_name}'s notes", slug=slug, description="A public notebook.")
    db.add(blog)
    db.flush()
    return user, blog


def _post(db: Session, author: User, blog: Blog, title: str, excerpt: str, body: str, tags: list[str], published: bool) -> Post:
    post = Post(
        blog_id=blog.id,
        author_id=author.id,
        title=title,
        slug=slugify(title),
        excerpt=excerpt,
        body=body,
        status="published" if published else "draft",
        published_at=utcnow() if published else None,
        updated_at=utcnow(),
    )
    for name in tags:
        tag = db.scalar(select(Tag).where(Tag.name == name))
        if tag is None:
            tag = Tag(name=name)
            db.add(tag)
            db.flush()
        post.tags.append(tag)
    db.add(post)
    db.flush()
    return post
