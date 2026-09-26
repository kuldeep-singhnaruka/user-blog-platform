"""Core flows: public reading, ownership, likes, comments, export, RBAC, uploads."""

from sqlalchemy import select

from app.core.database import SessionLocal
from app.core.permissions import has_permission
from app.core.rate_limit import RateLimiter
from app.models import User
from app.services.pdf_builder import build_pdf

PNG = bytes.fromhex(
    "89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c489"
    "0000000a49444154789c63000100000500010d0a2db40000000049454e44ae426082"
)


def auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def register(client, email: str, name: str = "Test User") -> dict:
    response = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "Passw0rd!", "display_name": name},
    )
    assert response.status_code == 201, response.text
    return response.json()


def set_role(email: str, role: str) -> None:
    db = SessionLocal()
    user = db.scalar(select(User).where(User.email == email))
    assert user is not None
    user.role = role
    db.commit()
    db.close()


def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["database"] == "ok"


def test_public_feed_hides_drafts_and_requires_login_to_write(client):
    writer = register(client, "writer@test.dev", "Writer One")
    created = client.post(
        "/api/v1/posts",
        json={"title": "Hidden draft", "body": "Not ready for the reading room.", "tags": ["notes"]},
        headers=auth(writer["access_token"]),
    )
    assert created.status_code == 201, created.text
    slug = created.json()["slug"]

    public = client.get(f"/api/v1/posts/by-slug/{slug}")
    assert public.status_code == 404

    anonymous = client.post("/api/v1/posts", json={"title": "Nope", "body": "Cannot."})
    assert anonymous.status_code == 401

    feed = client.get("/api/v1/posts")
    assert feed.status_code == 200
    assert all(item["slug"] != slug for item in feed.json()["data"])


def test_publish_like_comment_and_ownership(client):
    author = register(client, "author@test.dev", "Ada Author")
    reader = register(client, "reader@test.dev", "Reed Reader")
    headers = auth(author["access_token"])
    created = client.post(
        "/api/v1/posts?publish=true",
        json={
            "title": "Public essay",
            "body": "A short published piece about careful APIs.",
            "tags": ["api", "rest"],
            "excerpt": "Careful APIs stay small.",
        },
        headers=headers,
    )
    assert created.status_code == 201, created.text
    post = created.json()
    assert post["status"] == "published"
    assert post["blog_slug"]

    listed = client.get("/api/v1/posts?q=careful")
    assert listed.status_code == 200
    body = listed.json()
    assert body["meta"]["total"] >= 1
    assert any(item["id"] == post["id"] for item in body["data"])
    assert "body" not in body["data"][0]

    detail = client.get(f"/api/v1/posts/by-slug/{post['slug']}")
    assert detail.status_code == 200
    assert "careful APIs" in detail.json()["body"]

    forbidden = client.put(
        f"/api/v1/posts/{post['id']}",
        json={"title": "Stolen", "body": "This should fail the ownership check."},
        headers=auth(reader["access_token"]),
    )
    assert forbidden.status_code == 403

    liked = client.post(f"/api/v1/posts/{post['id']}/likes", headers=auth(reader["access_token"]))
    assert liked.status_code == 200, liked.text
    assert liked.json() == {"liked": True, "like_count": 1}
    again = client.post(f"/api/v1/posts/{post['id']}/likes", headers=auth(reader["access_token"]))
    assert again.json()["liked"] is False

    comment = client.post(
        f"/api/v1/posts/{post['id']}/comments",
        json={"body": "Useful distinction."},
        headers=auth(reader["access_token"]),
    )
    assert comment.status_code == 201, comment.text
    comment_id = comment.json()["id"]

    outsider_delete = client.delete(f"/api/v1/comments/{comment_id}", headers=headers)
    assert outsider_delete.status_code == 403

    set_role("author@test.dev", "moderator")
    moderated = client.delete(f"/api/v1/comments/{comment_id}", headers=headers)
    assert moderated.status_code == 204


def test_export_upload_and_admin_gate(client):
    owner = register(client, "owner@test.dev", "Owen Owner")
    headers = auth(owner["access_token"])
    client.post(
        "/api/v1/posts?publish=true",
        json={"title": "Export me", "body": "Row that should appear in the file."},
        headers=headers,
    )
    exported = client.get("/api/v1/me/export?format=csv", headers=headers)
    assert exported.status_code == 200
    assert "Export me" in exported.text

    pdf = client.get("/api/v1/me/export?format=pdf", headers=headers)
    assert pdf.status_code == 200
    assert pdf.content.startswith(b"%PDF")

    sheet = client.get("/api/v1/me/export?format=xlsx", headers=headers)
    assert sheet.status_code == 200
    assert sheet.content.startswith(b"PK")

    rejected = client.post(
        "/api/v1/uploads/cover",
        files={"file": ("notes.txt", b"hello", "text/plain")},
        headers=headers,
    )
    assert rejected.status_code == 400

    uploaded = client.post(
        "/api/v1/uploads/cover",
        files={"file": ("dot.png", PNG, "image/png")},
        headers=headers,
    )
    assert uploaded.status_code == 201, uploaded.text
    cover_url = uploaded.json()["cover_url"]
    media = client.get(cover_url)
    assert media.status_code == 200
    assert media.content.startswith(b"\x89PNG")

    audit = client.get("/api/v1/admin/audit", headers=headers)
    assert audit.status_code == 403

    set_role("owner@test.dev", "admin")
    audit_ok = client.get("/api/v1/admin/audit", headers=headers)
    assert audit_ok.status_code == 200
    assert audit_ok.json()["meta"]["total"] >= 1

    plan = client.get("/api/v1/admin/query-plan", headers=headers)
    assert plan.status_code == 200
    assert "ix_posts_status_published_at" in plan.json()["index_hint"]

    users = client.get("/api/v1/admin/users", headers=headers)
    assert users.status_code == 200
    assert any(row["email"] == "owner@test.dev" for row in users.json())


def test_oauth_token_and_webhook(client):
    register(client, "token@test.dev", "Token User")
    token = client.post("/api/v1/auth/token", data={"username": "token@test.dev", "password": "Passw0rd!"})
    assert token.status_code == 200, token.text
    assert token.json()["token_type"] == "bearer"

    missing = client.post("/api/v1/webhooks/events", json={"source": "demo", "event_type": "ping", "data": {}})
    assert missing.status_code == 401

    accepted = client.post(
        "/api/v1/webhooks/events",
        json={"source": "demo", "event_type": "ping", "data": {"ok": True}},
        headers={"X-Webhook-Token": "test-webhook-secret"},
    )
    assert accepted.status_code == 202, accepted.text


def test_reference_failure_still_publishes(client, monkeypatch):
    def explode(_topic: str):
        raise TimeoutError("upstream too slow")

    monkeypatch.setattr("app.services.post_service.fetch_topic_summary", explode)
    writer = register(client, "topic@test.dev", "Topic Writer")
    created = client.post(
        "/api/v1/posts?publish=true",
        json={"title": "With a topic", "body": "Still publishes when lookup fails.", "reference_topic": "HTTP"},
        headers=auth(writer["access_token"]),
    )
    assert created.status_code == 201, created.text
    assert created.json()["reference_extract"] is None


def test_permissions_and_pdf_unit():
    assert has_permission("user", "like:toggle")
    assert not has_permission("user", "audit:read")
    assert has_permission("admin", "audit:read")
    assert has_permission("moderator", "comment:moderate")
    assert not has_permission("moderator", "user:read")

    limiter = RateLimiter()
    assert limiter.allow("k", 1)
    assert not limiter.allow("k", 1)

    document = build_pdf(["Fieldnotes", "Second line"])
    assert document.startswith(b"%PDF")
