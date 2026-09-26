"""User and blog persistence."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Blog, User


class UserRepository:
    def __init__(self, db: Session):
        self.db = db

    def by_email(self, email: str) -> User | None:
        return self.db.scalar(select(User).where(User.email == email))

    def by_id(self, user_id: int) -> User | None:
        return self.db.get(User, user_id)

    def add(self, user: User) -> User:
        self.db.add(user)
        self.db.flush()
        return user

    def list_users(self) -> list[User]:
        return list(self.db.scalars(select(User).order_by(User.created_at.desc())))


class BlogRepository:
    def __init__(self, db: Session):
        self.db = db

    def by_owner(self, owner_id: int) -> Blog | None:
        return self.db.scalar(select(Blog).where(Blog.owner_id == owner_id))

    def by_slug(self, slug: str) -> Blog | None:
        return self.db.scalar(select(Blog).where(Blog.slug == slug))

    def slug_taken(self, slug: str) -> bool:
        return self.db.scalar(select(Blog.id).where(Blog.slug == slug)) is not None

    def add(self, blog: Blog) -> Blog:
        self.db.add(blog)
        self.db.flush()
        return blog
