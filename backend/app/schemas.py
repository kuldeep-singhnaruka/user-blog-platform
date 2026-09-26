"""Request and response contracts for the versioned API."""

import re
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ErrorDetail(BaseModel):
    code: str
    message: str
    details: object | None = None


class ErrorResponse(BaseModel):
    error: ErrorDetail


class PageMeta(BaseModel):
    page: int
    page_size: int
    total: int


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    display_name: str
    role: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


class RegisterIn(BaseModel):
    email: str = Field(min_length=3, max_length=255)
    password: str = Field(min_length=8, max_length=128)
    display_name: str = Field(min_length=2, max_length=80)

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        email = value.strip().lower()
        if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email):
            raise ValueError("Enter a valid email address")
        return email

    @field_validator("display_name")
    @classmethod
    def clean_name(cls, value: str) -> str:
        name = " ".join(value.split())
        if len(name) < 2:
            raise ValueError("Display name is too short")
        return name


class LoginIn(BaseModel):
    email: str
    password: str

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        return value.strip().lower()


class BlogOut(BaseModel):
    id: int
    name: str
    slug: str
    description: str
    owner_display_name: str


class BlogUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=120)
    description: str | None = Field(default=None, max_length=300)


class PostSummary(BaseModel):
    id: int
    title: str
    slug: str
    excerpt: str
    status: str
    cover_url: str | None
    tags: list[str]
    author_display_name: str
    author_id: int
    blog_slug: str
    blog_name: str
    like_count: int
    comment_count: int
    published_at: datetime | None
    created_at: datetime
    updated_at: datetime


class PostDetail(PostSummary):
    body: str
    reference_topic: str | None = None
    reference_title: str | None = None
    reference_extract: str | None = None
    reference_url: str | None = None
    liked_by_me: bool = False
    can_edit: bool = False


class PostListResponse(BaseModel):
    data: list[PostSummary]
    meta: PageMeta


class PostWrite(BaseModel):
    title: str = Field(min_length=3, max_length=140)
    body: str = Field(min_length=1, max_length=20_000)
    excerpt: str | None = Field(default=None, max_length=300)
    tags: list[str] = Field(default_factory=list, max_length=5)
    cover_url: str | None = None
    reference_topic: str | None = Field(default=None, max_length=120)

    @field_validator("tags")
    @classmethod
    def clean_tags(cls, value: list[str]) -> list[str]:
        cleaned: list[str] = []
        for raw in value:
            tag = re.sub(r"\s+", " ", raw.strip().lower())
            if not tag:
                continue
            if len(tag) > 40:
                raise ValueError("Tags must be 40 characters or fewer")
            if tag not in cleaned:
                cleaned.append(tag)
        if len(cleaned) > 5:
            raise ValueError("Use at most 5 tags")
        return cleaned

    @field_validator("cover_url")
    @classmethod
    def local_cover_only(cls, value: str | None) -> str | None:
        if value is None or value == "":
            return None
        if not re.fullmatch(r"/media/[a-f0-9]{32}\.(jpg|png|gif|webp)", value):
            raise ValueError("Cover must be an uploaded image")
        return value


class CommentIn(BaseModel):
    body: str = Field(min_length=1, max_length=2000)

    @field_validator("body")
    @classmethod
    def clean_body(cls, value: str) -> str:
        text = value.strip()
        if not text:
            raise ValueError("Comment cannot be empty")
        return text


class CommentOut(BaseModel):
    id: int
    body: str
    created_at: datetime
    author_id: int
    author_display_name: str
    can_delete: bool


class LikeOut(BaseModel):
    liked: bool
    like_count: int


class UploadOut(BaseModel):
    cover_url: str
    filename: str


class TagCount(BaseModel):
    name: str
    count: int


class AuditOut(BaseModel):
    id: int
    actor_id: int | None
    action: str
    resource_type: str
    resource_id: str
    detail: str
    created_at: datetime


class AuditListResponse(BaseModel):
    data: list[AuditOut]
    meta: PageMeta


class PermissionRow(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    role: str
    permission: str


class WebhookIn(BaseModel):
    source: str = Field(min_length=1, max_length=80)
    event_type: str = Field(min_length=1, max_length=80)
    data: dict = Field(default_factory=dict)


class WebhookOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    source: str
    event_type: str
    payload: str
    received_at: datetime


class HealthOut(BaseModel):
    status: str
    database: str
    uptime_seconds: float
