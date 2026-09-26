# Usage guide

## Run it locally

1. Create a virtualenv and install `backend/requirements.txt` (see the root README).
2. Start the API from the `backend` directory on port 8000.
3. Start the frontend with `npm run dev` from `frontend`.
4. Open http://localhost:5173.

The first API start creates tables and the demo reading room.

## Read without an account

Open the home page. Search, filter by tag, or filter by an author's blog slug. Open a note. Drafts are absent. Likes and comments ask you to sign in.

## Write as yourself

Register, or sign in as `mina@fieldnotes.local` / `Author123!`.

- **My desk** lists drafts and published notes.
- **Write** creates a note. Save draft keeps it off the public feed. Publish puts it in the reading room.
- A cover must be an image of 2 MB or less.
- Reference topic optionally asks Wikipedia for a short public summary. If that call fails, the note still saves.
- The blog description on My desk is your tenant profile. The slug stays fixed so existing links keep working.

Sign in as `ravi@fieldnotes.local` / `Reader123!` in a private window if you want a second person liking and commenting. You cannot edit Mina's notes with Ravi's account.

## Export

On My desk, export CSV, Excel, or PDF. The file contains only your posts.

## Admin

Sign in as `admin@fieldnotes.local` / `Admin123!`. The Admin link shows:

- the role to permission map
- accounts
- the audit log (register, login, publish, like, export, and so on)
- the SQL plan for the published feed

## Reset local data

Stop the API and delete `backend/data/blog.db`. The next start seeds the demo again. Uploaded images live in `backend/uploads/`.

## Configuration

Copy `.env.example` to `.env` at the project root.

| Variable | Why it exists |
| --- | --- |
| `JWT_SECRET` | Signs access tokens. Use a long random value if anyone else can reach the process. |
| `DATABASE_URL` | Default SQLite. Docker Compose sets PostgreSQL. |
| `WEBHOOK_SECRET` | Shared secret for inbound webhooks. |
| `EXTERNAL_API_BASE` / `EXTERNAL_API_KEY` | Optional second summary provider. Leave blank to use Wikipedia only. |
| `SEED_DEMO_DATA` | Set `false` to start with an empty database (permissions are still loaded). |

## Backup

SQLite:

```bash
cd backend
../.venv/bin/python scripts/backup_db.py
```

PostgreSQL:

```bash
pg_dump "postgresql://blog:blog@localhost:5432/blog" --format=custom --file=backups/blog.dump
```

## Send a webhook

```bash
curl -X POST http://localhost:8000/api/v1/webhooks/events \
  -H "Content-Type: application/json" \
  -H "X-Webhook-Token: dev-webhook-secret" \
  -d '{"source":"demo","event_type":"ping","data":{"ok":true}}'
```

Use the secret from your environment if you changed it.
