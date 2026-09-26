"""Copy the local SQLite database into backups/.

PostgreSQL deployments should use pg_dump instead:

    pg_dump "$DATABASE_URL" --format=custom --file=backups/blog.dump
"""

import shutil
from datetime import datetime, timezone
from pathlib import Path

from app.core.config import settings


def main() -> None:
    url = settings.resolved_database_url()
    if not url.startswith("sqlite///") and not url.startswith("sqlite:///"):
        raise SystemExit("This helper copies SQLite files. For PostgreSQL, use pg_dump.")
    source = Path(url.split("///", 1)[1])
    if not source.exists():
        raise SystemExit(f"Database file not found: {source}")
    destination_dir = Path(__file__).resolve().parents[2] / "backups"
    destination_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    target = destination_dir / f"blog-{stamp}.db"
    shutil.copy2(source, target)
    print(target)


if __name__ == "__main__":
    main()
