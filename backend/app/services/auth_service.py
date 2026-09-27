"""Register and login. Each new user gets one blog."""

from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.core.security import create_access_token, hash_password, verify_or_dummy
from app.models import Blog, User
from app.repositories.users import BlogRepository, UserRepository
from app.schemas import LoginIn, RegisterIn, TokenResponse, UserOut
from app.services.slugs import slugify


class AuthService:
    def __init__(self, db: Session):
        self.db = db
        self.users = UserRepository(db)
        self.blogs = BlogRepository(db)

    def register(self, payload: RegisterIn) -> TokenResponse:
        if self.users.by_email(payload.email):
            raise AppError(409, "email_taken", "An account with that email already exists")
        user = self.users.add(
            User(
                email=payload.email,
                password_hash=hash_password(payload.password),
                display_name=payload.display_name,
            )
        )
        self.blogs.add(
            Blog(
                owner_id=user.id,
                name=f"{payload.display_name}'s notes",
                slug=self._unique_blog_slug(payload.display_name),
            )
        )
        return self._token(user)

    def login(self, payload: LoginIn) -> TokenResponse:
        user = self.users.by_email(payload.email)
        password_ok = verify_or_dummy(payload.password, user.password_hash if user else None)
        if user is None or not password_ok:
            raise AppError(401, "invalid_credentials", "Invalid email or password")
        return self._token(user)

    def _unique_blog_slug(self, name: str) -> str:
        base = slugify(name)
        slug = base
        suffix = 2
        while self.blogs.slug_taken(slug):
            slug = f"{base}-{suffix}"
            suffix += 1
        return slug

    def _token(self, user: User) -> TokenResponse:
        return TokenResponse(access_token=create_access_token(user.id), user=UserOut.model_validate(user))
