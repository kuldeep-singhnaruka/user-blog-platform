"""Admin and moderator oversight: users, permissions, audit, and query plans."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import require_permission
from app.models import AuditLog, RolePermission, User
from app.schemas import AuditListResponse, AuditOut, PageMeta, PermissionRow, UserOut

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/users", response_model=list[UserOut])
def list_users(_admin: User = Depends(require_permission("user:read")), db: Session = Depends(get_db)) -> list[User]:
    return list(db.scalars(select(User).order_by(User.id.asc())))


@router.get("/permissions", response_model=list[PermissionRow])
def list_permissions(
    _admin: User = Depends(require_permission("permission:read")),
    db: Session = Depends(get_db),
) -> list[RolePermission]:
    return list(db.scalars(select(RolePermission).order_by(RolePermission.role, RolePermission.permission)))


@router.get("/audit", response_model=AuditListResponse)
def list_audit(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    _admin: User = Depends(require_permission("audit:read")),
    db: Session = Depends(get_db),
) -> AuditListResponse:
    from sqlalchemy import func

    total = db.scalar(select(func.count()).select_from(AuditLog)) or 0
    rows = list(
        db.scalars(
            select(AuditLog).order_by(AuditLog.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
        )
    )
    data = [
        AuditOut(
            id=row.id,
            actor_id=row.actor_id,
            action=row.action,
            resource_type=row.resource_type,
            resource_id=row.resource_id,
            detail=row.detail,
            created_at=row.created_at,
        )
        for row in rows
    ]
    return AuditListResponse(data=data, meta=PageMeta(page=page, page_size=page_size, total=int(total)))


@router.get("/query-plan")
def query_plan(_admin: User = Depends(require_permission("query:explain")), db: Session = Depends(get_db)) -> dict:
    """Show how the published-post list uses the composite status/date index."""
    sql = "SELECT id, title FROM posts WHERE status = 'published' ORDER BY published_at DESC LIMIT 10"
    if db.get_bind().dialect.name == "sqlite":
        rows = db.execute(text(f"EXPLAIN QUERY PLAN {sql}")).all()
        plan = [tuple(row) for row in rows]
    else:
        rows = db.execute(text(f"EXPLAIN {sql}")).all()
        plan = [tuple(str(cell) for cell in row) for row in rows]
    return {
        "sql": sql,
        "plan": plan,
        "index_hint": "ix_posts_status_published_at covers status + published_at",
    }
