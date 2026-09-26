"""Fieldnotes HTTP application: versioned JSON API, media, health, and metrics."""

import logging
import time
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import FileResponse, JSONResponse, PlainTextResponse

from app import models  # noqa: F401  (register tables)
from app.api.router import api_router
from app.core.config import settings
from app.core.database import Base, SessionLocal, engine
from app.core.errors import AppError, error_body
from app.core.rate_limit import limiter
from app.seed import seed_database
from app.services.files import media_file

logger = logging.getLogger("fieldnotes")
STARTED_AT = time.time()
SKIP_LIMIT = {"/health", "/metrics"}


class Metrics:
    def __init__(self) -> None:
        self.total = 0
        self.by_status: dict[str, int] = {}

    def record(self, status_code: int) -> None:
        self.total += 1
        key = str(status_code)
        self.by_status[key] = self.by_status.get(key, 0) + 1

    def render(self) -> str:
        lines = [
            "# HELP http_requests_total HTTP responses served by this process",
            "# TYPE http_requests_total counter",
            f"http_requests_total {self.total}",
        ]
        for code, count in sorted(self.by_status.items()):
            lines.append(f'http_responses{{status="{code}"}} {count}')
        lines.append(f"process_uptime_seconds {time.time() - STARTED_AT:.0f}")
        return "\n".join(lines) + "\n"


metrics = Metrics()


@asynccontextmanager
async def lifespan(_app: FastAPI):
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
    Base.metadata.create_all(bind=engine)
    settings.resolved_upload_dir()
    db = SessionLocal()
    try:
        seed_database(db)
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
    if len(settings.jwt_secret) < 24:
        logger.warning("JWT_SECRET is short. Set a long random value in the root .env file.")
    yield


app = FastAPI(
    title="Fieldnotes API",
    version="1.0.0",
    description="User-specific blog platform. Public reading, authenticated writing, likes, and comments.",
    lifespan=lifespan,
)
app.add_middleware(GZipMiddleware, minimum_size=800)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(api_router)


@app.middleware("http")
async def observe(request: Request, call_next):
    if request.method != "OPTIONS" and request.url.path not in SKIP_LIMIT:
        client = request.client.host if request.client else "unknown"
        if request.url.path.endswith("/auth/login") or request.url.path.endswith("/auth/token"):
            allowed = limiter.allow(f"login:{client}", settings.login_rate_limit_per_minute)
        else:
            allowed = limiter.allow(f"ip:{client}", settings.rate_limit_per_minute)
        if not allowed:
            response = JSONResponse(
                status_code=429,
                content=error_body("rate_limited", "Too many requests. Try again in a minute."),
                headers={"Retry-After": "60"},
            )
            origin = request.headers.get("origin")
            if origin in settings.cors_origin_list:
                response.headers["Access-Control-Allow-Origin"] = origin
            return response

    started = time.perf_counter()
    request_id = request.headers.get("x-request-id") or uuid.uuid4().hex
    try:
        response = await call_next(request)
    except Exception:
        metrics.record(500)
        logger.exception("request failed rid=%s", request_id)
        raise
    metrics.record(response.status_code)
    response.headers["X-Request-Id"] = request_id
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "same-origin"
    elapsed_ms = (time.perf_counter() - started) * 1000
    logger.info("%s %s %s %.1fms rid=%s", request.method, request.url.path, response.status_code, elapsed_ms, request_id)
    return response


@app.exception_handler(AppError)
async def app_error_handler(_request: Request, exc: AppError) -> JSONResponse:
    return JSONResponse(status_code=exc.status_code, content=error_body(exc.code, exc.message, exc.details))


@app.exception_handler(RequestValidationError)
async def validation_handler(_request: Request, exc: RequestValidationError) -> JSONResponse:
    return JSONResponse(
        status_code=422,
        content=error_body("validation_error", "Request validation failed", jsonable_encoder(exc.errors())),
    )


@app.get("/health")
def health():
    from sqlalchemy import text

    database = "ok"
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
    except Exception:
        database = "down"
        return JSONResponse(
            status_code=503,
            content={"status": "degraded", "database": database, "uptime_seconds": round(time.time() - STARTED_AT, 1)},
        )
    return {"status": "ok", "database": database, "uptime_seconds": round(time.time() - STARTED_AT, 1)}


@app.get("/metrics")
def metrics_view() -> PlainTextResponse:
    return PlainTextResponse(metrics.render(), media_type="text/plain; version=0.0.4")


@app.get("/media/{filename}")
def download_media(filename: str) -> FileResponse:
    path = media_file(filename)
    return FileResponse(path)


@app.get("/")
def root() -> dict:
    return {"service": settings.app_name, "docs": "/docs", "health": "/health"}

