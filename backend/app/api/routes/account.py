"""Uploads, exports, and inbound webhooks."""

import json

from fastapi import APIRouter, Depends, File, Header, Query, UploadFile
from fastapi.responses import Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.deps import require_permission
from app.core.errors import AppError
from app.models import User, WebhookEvent
from app.schemas import UploadOut, WebhookIn, WebhookOut
from app.services.audit_service import AuditService
from app.services.export_service import ExportService
from app.services.files import save_cover

router = APIRouter(tags=["account"])


@router.post("/uploads/cover", response_model=UploadOut, status_code=201)
async def upload_cover(
    file: UploadFile = File(...),
    user: User = Depends(require_permission("upload:create")),
    db: Session = Depends(get_db),
) -> UploadOut:
    data = await file.read(settings.max_upload_bytes + 1)
    cover_url = save_cover(data)
    AuditService(db).record(
        actor_id=user.id,
        action="upload.create",
        resource_type="file",
        resource_id=cover_url,
    )
    return UploadOut(cover_url=cover_url, filename=cover_url.rsplit("/", 1)[-1])


@router.get("/me/export")
def export_posts(
    export_format: str = Query("csv", alias="format", pattern="^(csv|xlsx|pdf)$"),
    user: User = Depends(require_permission("export:own")),
    db: Session = Depends(get_db),
) -> Response:
    payload, media_type, filename = ExportService(db).render(user, export_format)
    return Response(
        content=payload,
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.post("/webhooks/events", response_model=WebhookOut, status_code=202)
def receive_webhook(
    payload: WebhookIn,
    x_webhook_token: str | None = Header(default=None),
    db: Session = Depends(get_db),
) -> WebhookEvent:
    import hmac

    supplied = x_webhook_token or ""
    if not hmac.compare_digest(supplied, settings.webhook_secret):
        raise AppError(401, "unauthorized", "Invalid webhook token")
    event = WebhookEvent(
        source=payload.source.strip(),
        event_type=payload.event_type.strip(),
        payload=json.dumps(payload.data)[:4000],
    )
    db.add(event)
    db.flush()
    return event


@router.get("/admin/webhooks", response_model=list[WebhookOut])
def list_webhooks(
    _user: User = Depends(require_permission("webhook:read")),
    db: Session = Depends(get_db),
) -> list[WebhookEvent]:
    return list(db.scalars(select(WebhookEvent).order_by(WebhookEvent.received_at.desc()).limit(50)))
