"""Validate uploaded images and keep them inside the upload directory."""

import secrets
from pathlib import Path

from app.core.config import settings
from app.core.errors import AppError

_SIGNATURES = (
    (b"\xff\xd8\xff", "jpg"),
    (b"\x89PNG\r\n\x1a\n", "png"),
    (b"GIF87a", "gif"),
    (b"GIF89a", "gif"),
)


def sniff_image(data: bytes) -> str | None:
    for signature, kind in _SIGNATURES:
        if data.startswith(signature):
            return kind
    if len(data) >= 12 and data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "webp"
    return None


def save_cover(data: bytes) -> str:
    if len(data) == 0:
        raise AppError(400, "empty_file", "The uploaded file is empty")
    if len(data) > settings.max_upload_bytes:
        raise AppError(413, "file_too_large", "Images must be 2 MB or smaller")
    kind = sniff_image(data)
    if kind is None:
        raise AppError(400, "bad_file_type", "Upload a JPEG, PNG, GIF, or WebP image")
    filename = f"{secrets.token_hex(16)}.{kind}"
    destination = settings.resolved_upload_dir() / filename
    destination.write_bytes(data)
    return f"/media/{filename}"


def media_file(filename: str) -> Path:
    """Resolve a public media name and refuse anything that leaves the upload directory."""
    safe_name = Path(filename).name
    if safe_name != filename:
        raise AppError(404, "not_found", "File not found")
    root = settings.resolved_upload_dir().resolve()
    path = (root / safe_name).resolve()
    if root not in path.parents or not path.is_file():
        raise AppError(404, "not_found", "File not found")
    return path
