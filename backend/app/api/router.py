"""Versioned API surface."""

from fastapi import APIRouter

from app.api.routes import account, admin, auth, engagement, posts

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth.router)
api_router.include_router(posts.router)
api_router.include_router(engagement.router)
api_router.include_router(account.router)
api_router.include_router(admin.router)
