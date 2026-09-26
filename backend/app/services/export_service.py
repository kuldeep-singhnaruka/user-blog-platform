"""CSV, Excel, and PDF downloads of the caller's own posts."""

import csv
from io import BytesIO, StringIO

from openpyxl import Workbook
from sqlalchemy.orm import Session

from app.models import User
from app.repositories.posts import PostRepository
from app.services.audit_service import AuditService
from app.services.pdf_builder import build_pdf

COLUMNS = ["id", "title", "slug", "status", "published_at", "excerpt"]


class ExportService:
    def __init__(self, db: Session):
        self.db = db
        self.posts = PostRepository(db)
        self.audit = AuditService(db)

    def render(self, user: User, export_format: str) -> tuple[bytes, str, str]:
        rows = [self._row(post) for post in self.posts.for_author(user.id)]
        self.audit.record(
            actor_id=user.id,
            action="export.download",
            resource_type="user",
            resource_id=user.id,
            detail=export_format,
        )
        if export_format == "csv":
            return self._csv(rows), "text/csv; charset=utf-8", "my-posts.csv"
        if export_format == "xlsx":
            return self._xlsx(rows), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", "my-posts.xlsx"
        if export_format == "pdf":
            return self._pdf(user.display_name, rows), "application/pdf", "my-posts.pdf"
        raise ValueError(export_format)

    def _row(self, post) -> list[str]:
        published = post.published_at.isoformat(sep=" ", timespec="minutes") if post.published_at else ""
        return [str(post.id), post.title, post.slug, post.status, published, post.excerpt]

    def _csv(self, rows: list[list[str]]) -> bytes:
        buffer = StringIO()
        writer = csv.writer(buffer)
        writer.writerow(COLUMNS)
        writer.writerows(rows)
        return buffer.getvalue().encode("utf-8")

    def _xlsx(self, rows: list[list[str]]) -> bytes:
        workbook = Workbook()
        sheet = workbook.active
        sheet.title = "Posts"
        sheet.append(COLUMNS)
        for row in rows:
            sheet.append(row)
        buffer = BytesIO()
        workbook.save(buffer)
        return buffer.getvalue()

    def _pdf(self, display_name: str, rows: list[list[str]]) -> bytes:
        lines = [f"Fieldnotes export for {display_name}", ""]
        if not rows:
            lines.append("No posts yet.")
        for row in rows:
            lines.append(f"{row[3].upper()}  {row[1]}")
            lines.append(f"Slug: {row[2]}    Published: {row[4] or '-'}")
            lines.append(row[5])
            lines.append("")
        return build_pdf(lines)
