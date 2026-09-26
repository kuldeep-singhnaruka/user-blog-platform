# Fieldnotes

A user-specific blog platform for the Week 1 production-engineering bootcamp.

Anyone can browse and read published notes. Signed-in users get their own blog (a tenant), can draft and publish posts, and can like or comment on other people's published work. Owners manage only their own posts. Moderators and admins have a shorter, explicit permission list.

The app runs on your machine. A public domain is not required.

## Quick start

From the project root:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
cd backend
uvicorn app.main:app --reload --port 8000
```

In a second terminal:

```bash
cd frontend
npm install
npm run dev
```

Open [http://localhost:5173](http://localhost:5173).

API docs (Swagger): [http://localhost:8000/docs](http://localhost:8000/docs)

Health check: [http://localhost:8000/health](http://localhost:8000/health)

No `.env` file is required for this local path. Defaults use SQLite at `backend/data/blog.db`. Copy `.env.example` to `.env` when you want to change the JWT secret or database.

## Demo accounts

Created on first launch when `SEED_DEMO_DATA` is true (the default):

| Email | Password | What they can do |
| --- | --- | --- |
| `mina@fieldnotes.local` | `Author123!` | Author. Has published notes and one draft. |
| `ravi@fieldnotes.local` | `Reader123!` | Reader. Can like and comment. |
| `admin@fieldnotes.local` | `Admin123!` | Admin. Audit log, users, permissions, query plan. |

## Tests

```bash
cd backend
../.venv/bin/pytest
```

## Docker (optional)

Requires Docker. This path uses PostgreSQL instead of SQLite.

```bash
docker compose up --build
```

The site is at [http://localhost:5173](http://localhost:5173) and the API at [http://localhost:8000](http://localhost:8000).

## Documentation

- [Architecture](docs/ARCHITECTURE.md)
- [API contracts](docs/API.md)
- [Usage guide](docs/USAGE.md)
- [2-minute demo script](docs/DEMO.md)

## What the layout is teaching

| Idea | Where it lives |
| --- | --- |
| Client / server and HTTP | React app on port 5173, FastAPI on port 8000 |
| MVC-style split | `api/routes` (controllers), `services`, `models`, `repositories` |
| REST | `/api/v1`, resources, status codes, pagination, filter, sort |
| Auth vs authorization | JWT identifies the user. Roles and permissions decide the action. |
| Multi-tenant ownership | Each user owns one blog. Post writes use that blog, never a client-supplied tenant id. |
| Uploads | `POST /api/v1/uploads/cover` checks type and size, stores a random filename |
| Export | CSV, Excel, and PDF of the caller's own posts |
| Performance | Composite index, list payload without the body, grouped like/comment counts, short list cache, gzip, rate limit |
| RBAC | `user`, `moderator`, `admin` in `app/core/permissions.py` and the `role_permissions` table |
| Third-party HTTP | Wikipedia summary lookup with timeout and retries. Optional API key provider via env. |
| Webhooks | `POST /api/v1/webhooks/events` with a shared secret |
| OAuth2 token route | `POST /api/v1/auth/token` (password grant for this first-party app; see the docs for why third parties should use authorization code + PKCE) |
| Containers and CI | `docker-compose.yml`, health check, `.github/workflows/ci.yml` |
| Backups | `python backend/scripts/backup_db.py` for SQLite. PostgreSQL: `pg_dump`. |
| Audit | `audit_logs` table, visible to admins |

## Project map

```text
backend/app/
  api/routes/        HTTP controllers
  services/          business rules
  repositories/      database queries
  models/            tables
  core/              config, security, permissions, rate limit
frontend/src/        reading room, editor, desk, admin
docs/                architecture, API, usage, demo script
```
