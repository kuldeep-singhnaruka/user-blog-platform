"""User and blog lookups."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Blog, User


class UserRepository:
    def __init__(self, db: Session):
        self.db = db

    def by_email(self, email: str) -> User | None:
        return self.db.scalar(select(User).where(User.email == email))

    def add(self, user: User) -> User:
        self.db.add(user)
        self.db.flush()
        return user


class BlogRepository:
    def __init__(self, db: Session):
        self.db = db

    def slug_taken(self, slug: str) -> bool:
        return self.db.scalar(select(Blog.id).where(Blog.slug == slug)) is not None

    def add(self, blog: Blog) -> Blog:
        self.db.add(blog)
        self.db.flush()
        return blog
