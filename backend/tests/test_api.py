"""Public reading, ownership, likes, and comments."""


def auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def register(client, email: str, name: str = "Test User") -> dict:
    response = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "Passw0rd!", "display_name": name},
    )
    assert response.status_code == 201, response.text
    return response.json()


def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["database"] == "ok"


def test_public_feed_hides_drafts(client):
    writer = register(client, "writer@test.dev", "Writer One")
    created = client.post(
        "/api/v1/posts",
        json={"title": "Hidden draft", "body": "Not ready for the reading room."},
        headers=auth(writer["access_token"]),
    )
    assert created.status_code == 201, created.text
    slug = created.json()["slug"]

    assert client.get(f"/api/v1/posts/by-slug/{slug}").status_code == 404
    assert client.post("/api/v1/posts", json={"title": "Nope", "body": "Cannot."}).status_code == 401

    feed = client.get("/api/v1/posts")
    assert feed.status_code == 200
    assert all(item["slug"] != slug for item in feed.json()["data"])


def test_publish_like_comment_and_ownership(client):
    author = register(client, "author@test.dev", "Ada Author")
    reader = register(client, "reader@test.dev", "Reed Reader")
    created = client.post(
        "/api/v1/posts?publish=true",
        json={"title": "Public essay", "body": "A short published piece about careful APIs.", "excerpt": "Careful APIs stay small."},
        headers=auth(author["access_token"]),
    )
    assert created.status_code == 201, created.text
    post = created.json()
    assert post["status"] == "published"

    listed = client.get("/api/v1/posts?q=careful")
    assert any(item["id"] == post["id"] for item in listed.json()["data"])
    assert "body" not in listed.json()["data"][0]

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
    assert liked.json() == {"liked": True, "like_count": 1}

    mine = client.get("/api/v1/me/posts", headers=auth(author["access_token"]))
    assert mine.status_code == 200
    owned = mine.json()
    assert owned["meta"]["total"] == 1
    assert owned["data"][0]["id"] == post["id"]
    assert owned["data"][0]["like_count"] == 1

    again = client.post(f"/api/v1/posts/{post['id']}/likes", headers=auth(reader["access_token"]))
    assert again.json()["liked"] is False

    comment = client.post(
        f"/api/v1/posts/{post['id']}/comments",
        json={"body": "Useful distinction."},
        headers=auth(reader["access_token"]),
    )
    assert comment.status_code == 201, comment.text
    removed = client.delete(f"/api/v1/comments/{comment.json()['id']}", headers=auth(reader["access_token"]))
    assert removed.status_code == 204

    author_cannot_delete_others = client.post(
        f"/api/v1/posts/{post['id']}/comments",
        json={"body": "Mine."},
        headers=auth(reader["access_token"]),
    )
    blocked = client.delete(
        f"/api/v1/comments/{author_cannot_delete_others.json()['id']}",
        headers=auth(author["access_token"]),
    )
    assert blocked.status_code == 403
