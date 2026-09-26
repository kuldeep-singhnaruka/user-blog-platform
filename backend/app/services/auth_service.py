"""Registration, login, and the caller's blog tenant."""

from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.core.security import create_access_token, hash_password, verify_or_dummy
from app.models import Blog, User
from app.repositories.users import BlogRepository, UserRepository
from app.schemas import BlogOut, BlogUpdate, LoginIn, RegisterIn, TokenResponse, UserOut
from app.services.audit_service import AuditService
from app.services.slugs import slugify


class AuthService:
    def __init__(self, db: Session):
        self.db = db
        self.users = UserRepository(db)
        self.blogs = BlogRepository(db)
        self.audit = AuditService(db)

    def register(self, payload: RegisterIn) -> TokenResponse:
        if self.users.by_email(payload.email):
            raise AppError(409, "email_taken", "An account with that email already exists")
        user = self.users.add(
            User(
                email=payload.email,
                password_hash=hash_password(payload.password),
                display_name=payload.display_name,
                role="user",
            )
        )
        blog = self.blogs.add(
            Blog(
                owner_id=user.id,
                name=f"{payload.display_name}'s notes",
                slug=self._unique_blog_slug(payload.display_name),
                description="",
            )
        )
        self.audit.record(
            actor_id=user.id,
            action="user.register",
            resource_type="user",
            resource_id=user.id,
            detail=blog.slug,
        )
        return self._token(user)

    def login(self, payload: LoginIn) -> TokenResponse:
        user = self.users.by_email(payload.email)
        password_ok = verify_or_dummy(payload.password, user.password_hash if user else None)
        if user is None or not user.is_active or not password_ok:
            self.audit.record(
                actor_id=user.id if user else None,
                action="user.login_failed",
                resource_type="user",
                resource_id=user.id if user else "",
                detail=payload.email,
            )
            self.db.commit()
            raise AppError(401, "invalid_credentials", "Invalid email or password")
        self.audit.record(actor_id=user.id, action="user.login", resource_type="user", resource_id=user.id)
        return self._token(user)

    def update_blog(self, user: User, payload: BlogUpdate) -> BlogOut:
        blog = self.blogs.by_owner(user.id)
        if blog is None:
            raise AppError(403, "no_tenant", "This account has no blog workspace")
        if payload.name is not None:
            blog.name = payload.name.strip()
        if payload.description is not None:
            blog.description = payload.description.strip()
        self.db.flush()
        self.audit.record(actor_id=user.id, action="blog.update", resource_type="blog", resource_id=blog.id)
        return self.present_blog(blog)

    def present_blog(self, blog: Blog) -> BlogOut:
        owner = blog.owner or self.users.by_id(blog.owner_id)
        return BlogOut(
            id=blog.id,
            name=blog.name,
            slug=blog.slug,
            description=blog.description,
            owner_display_name=owner.display_name if owner else "",
        )

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
