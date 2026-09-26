"""Append-only audit records. The request session commits them with the action."""

from sqlalchemy.orm import Session

from app.models import AuditLog


class AuditService:
    def __init__(self, db: Session):
        self.db = db

    def record(
        self,
        *,
        actor_id: int | None,
        action: str,
        resource_type: str,
        resource_id: str = "",
        detail: str = "",
    ) -> None:
        self.db.add(
            AuditLog(
                actor_id=actor_id,
                action=action,
                resource_type=resource_type,
                resource_id=str(resource_id),
                detail=detail[:500],
            )
        )
        self.db.flush()
