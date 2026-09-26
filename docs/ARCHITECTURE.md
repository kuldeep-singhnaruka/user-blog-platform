# Architecture

Fieldnotes is a small client-server system. The browser is the client. FastAPI is the server. PostgreSQL is optional; SQLite is the local default so the project runs without extra services.

```text
Browser (React, Vite :5173)
        |  HTTP JSON  /api/v1
        v
FastAPI
  middleware   rate limit, request id, gzip, CORS, access log
  routes       validate input, choose status code
  services     permissions, ownership, publishing rules
  repositories queries and indexes
  models       users, blogs, posts, comments, likes, audit
        |
        v
SQLite or PostgreSQL
local upload directory for cover images
```

## Request lifecycle

1. The browser calls the Vite dev server. Vite proxies `/api` and `/media` to port 8000, so the browser sees one origin.
2. Middleware assigns a request id, applies the per-IP rate limit, and later writes an access log line.
3. A route validates the body with Pydantic.
4. Auth dependencies read the bearer token, load the user from the database, and check a permission. The role inside the token is not trusted; the database role is.
5. A service applies the business rule. Writing a post always uses the caller's blog. The client cannot pass another tenant id.
6. A repository runs the SQL. The session commits if the route returns normally, and rolls back if it raises.
7. Errors use one envelope: `{ "error": { "code", "message", "details" } }`.

## Tenancy and ownership

A blog row is the tenant. Registration creates exactly one blog for the new user. Every post stores `blog_id` and `author_id`.

- Public routes see posts with `status = published` only.
- Drafts are visible to the author and to roles with `post:moderate`.
- Update and delete require `post:update_own` / `post:delete_own` plus matching `author_id`, or `post:moderate`.
- Likes and comments require a signed-in user and a published post. The commenter does not need to be the author.

## Roles

| Role | Extra capability beyond a normal user |
| --- | --- |
| user | Own posts, likes, comments, export, upload |
| moderator | Delete any comment, edit or delete any post |
| admin | Moderator rights, plus users, audit log, permission map, query plan, webhooks |

The map in `backend/app/core/permissions.py` is the source of truth. Startup copies it into `role_permissions` so the admin screen can show the stored mapping.

## Data and indexes

Published feeds filter on `status` and sort on `published_at`. The composite index `ix_posts_status_published_at` matches that query. Likes have a unique `(post_id, user_id)` constraint. Comments are indexed by `(post_id, created_at)`.

List responses omit the post body (smaller payload). Like and comment counts for a page are two grouped queries, not one query per card, which avoids an N+1 loop. A short in-memory cache sits in front of the public list and is cleared on writes.

`GET /api/v1/admin/query-plan` runs `EXPLAIN QUERY PLAN` (SQLite) or `EXPLAIN` (PostgreSQL) for the feed query.

## Files

Covers are checked by magic bytes, limited to 2 MB, and stored under a random name in `backend/uploads`. The public URL is `/media/{filename}`. Path traversal is rejected. Exports are generated in memory and only include the caller's posts.

## External HTTP and webhooks

On create or when the reference topic changes, the server may call Wikipedia's public summary API. The client sets a timeout and retries on transport errors and 429/5xx. A failure does not block publishing. If `EXTERNAL_API_BASE` and `EXTERNAL_API_KEY` are both set, that provider is tried first and the API key is sent as `X-Api-Key`.

Inbound webhooks hit `POST /api/v1/webhooks/events` and must present `X-Webhook-Token`. The shared secret is an environment variable, not a constant in the route.

## Auth

Passwords are stored as PBKDF2-HMAC-SHA256 hashes. Sessions are stateless JWTs signed with `JWT_SECRET`.

`POST /api/v1/auth/login` is JSON for the web app. `POST /api/v1/auth/token` is an OAuth2 password grant so Swagger's Authorize button works. Password grant is acceptable here because the client is first-party. A third-party application should use the authorization-code flow with PKCE and should never collect the user's password.

## Runtime

- `GET /health` checks the database.
- `GET /metrics` exposes a small Prometheus-style counter.
- Logs go to stdout (method, path, status, duration, request id).
- `docker-compose.yml` runs Postgres, the API, and nginx. The API image has a health check.
- GitHub Actions runs the pytest suite on push and pull request.
- `backend/scripts/backup_db.py` copies the SQLite file. Postgres backups use `pg_dump`.

## API versioning

All JSON resources live under `/api/v1`. A later breaking change can add `/api/v2` without moving the current routes.
