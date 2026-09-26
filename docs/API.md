# API contracts

Base URL: `http://localhost:8000`

Interactive schema: `GET /docs` and `GET /openapi.json`

All versioned routes are under `/api/v1`.

## Error envelope

```json
{
  "error": {
    "code": "forbidden",
    "message": "You cannot edit this post",
    "details": null
  }
}
```

| Status | When |
| --- | --- |
| 200 | Read or update succeeded |
| 201 | Resource created |
| 202 | Webhook accepted |
| 204 | Delete succeeded, empty body |
| 400 | Bad file or filter |
| 401 | Missing or invalid token, or bad webhook secret |
| 403 | Authenticated, but the role or owner does not allow it |
| 404 | Missing, or hidden because it is a draft |
| 409 | Email already registered |
| 413 | File larger than 2 MB |
| 422 | Body failed validation |
| 429 | Rate limit. `Retry-After: 60` |
| 503 | Database health check failed |

## Pagination

List routes return:

```json
{
  "data": [],
  "meta": { "page": 1, "page_size": 10, "total": 42 }
}
```

`page` starts at 1. `page_size` max is 50 on public lists and 100 on the audit log.

## Auth

`POST /api/v1/auth/register`

```json
{ "email": "mina@fieldnotes.local", "password": "Author123!", "display_name": "Mina Rao" }
```

`POST /api/v1/auth/login`

```json
{ "email": "mina@fieldnotes.local", "password": "Author123!" }
```

Both return:

```json
{
  "access_token": "<jwt>",
  "token_type": "bearer",
  "user": { "id": 1, "email": "mina@fieldnotes.local", "display_name": "Mina Rao", "role": "user" }
}
```

`POST /api/v1/auth/token` is form-encoded (`username`, `password`) for the OAuth2 password grant. `username` is the email.

Send `Authorization: Bearer <jwt>` on protected routes.

| Method | Path | Auth |
| --- | --- | --- |
| GET | `/api/v1/auth/me` | user |
| GET | `/api/v1/auth/me/blog` | user |
| PATCH | `/api/v1/auth/me/blog` | user. Body: `{ "name"?, "description"? }` |

## Posts

| Method | Path | Auth | Notes |
| --- | --- | --- | --- |
| GET | `/api/v1/posts` | public | Query: `page`, `page_size`, `q`, `tag`, `author` (blog slug), `sort` (`published_at`, `created_at`, `title`), `order` (`asc`, `desc`) |
| GET | `/api/v1/tags` | public | Tag name and published count |
| GET | `/api/v1/posts/by-slug/{slug}` | public | Drafts return 404 unless the caller may see them |
| GET | `/api/v1/blogs/{slug}` | public | Blog profile |
| GET | `/api/v1/me/posts` | user | Own posts, including drafts. Optional `status`. |
| POST | `/api/v1/posts?publish=false` | `post:create` | Create a draft. `publish=true` publishes immediately. |
| GET | `/api/v1/posts/{id}` | user | Author or moderator. 404 for everyone else if it is a draft. |
| PUT | `/api/v1/posts/{id}` | owner or moderator | Replaces editable fields. Slug stays stable. |
| POST | `/api/v1/posts/{id}/publish` | owner or moderator | |
| POST | `/api/v1/posts/{id}/unpublish` | owner or moderator | |
| DELETE | `/api/v1/posts/{id}` | owner or moderator | |

Create and update body:

```json
{
  "title": "A boundary is a feature",
  "body": "Full markdown text",
  "excerpt": "Optional",
  "tags": ["engineering"],
  "cover_url": "/media/<32 hex chars>.png",
  "reference_topic": "HTTP"
}
```

`cover_url` must be a file previously returned by the upload route, or null. List items omit `body`. Detail adds `body`, reference fields, `liked_by_me`, and `can_edit`.

## Engagement

| Method | Path | Auth |
| --- | --- | --- |
| GET | `/api/v1/posts/{id}/comments` | public for published posts |
| POST | `/api/v1/posts/{id}/comments` | `comment:create`. Body: `{ "body": "..." }` |
| DELETE | `/api/v1/comments/{id}` | author, or `comment:moderate` |
| POST | `/api/v1/posts/{id}/likes` | `like:toggle`. Toggles and returns `{ "liked": true, "like_count": 1 }` |

## Files and export

| Method | Path | Auth |
| --- | --- | --- |
| POST | `/api/v1/uploads/cover` | `upload:create`. Multipart field name `file`. JPEG, PNG, GIF, WebP. Max 2 MB. |
| GET | `/media/{filename}` | public |
| GET | `/api/v1/me/export?format=csv` | `export:own`. Also `xlsx` and `pdf`. |

## Admin and webhooks

| Method | Path | Auth |
| --- | --- | --- |
| GET | `/api/v1/admin/users` | `user:read` |
| GET | `/api/v1/admin/permissions` | `permission:read` |
| GET | `/api/v1/admin/audit?page=1` | `audit:read` |
| GET | `/api/v1/admin/query-plan` | `query:explain` |
| GET | `/api/v1/admin/webhooks` | `webhook:read` |
| POST | `/api/v1/webhooks/events` | Header `X-Webhook-Token` |

Webhook body:

```json
{ "source": "demo", "event_type": "ping", "data": { "ok": true } }
```

## Operations

| Method | Path | Purpose |
| --- | --- | --- |
| GET | `/health` | `{ "status", "database", "uptime_seconds" }` |
| GET | `/metrics` | Process counters |
| GET | `/` | Service name and doc links |
