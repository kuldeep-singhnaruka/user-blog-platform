"""Request and response shapes."""

import re
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    display_name: str


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


class PageMeta(BaseModel):
    page: int
    page_size: int
    total: int


class PostSummary(BaseModel):
    id: int
    title: str
    slug: str
    excerpt: str
    status: str
    author_display_name: str
    author_id: int
    blog_slug: str
    blog_name: str
    like_count: int
    comment_count: int
    published_at: datetime | None
    created_at: datetime


class PostDetail(PostSummary):
    body: str
    liked_by_me: bool = False
    can_edit: bool = False


class PostListResponse(BaseModel):
    data: list[PostSummary]
    meta: PageMeta


class PostWrite(BaseModel):
    title: str = Field(min_length=3, max_length=140)
    body: str = Field(min_length=1, max_length=20_000)
    excerpt: str | None = Field(default=None, max_length=300)


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
