"""Isolated SQLite database for the API suite. Environment is set before the app imports."""

import os
from pathlib import Path

TEST_ROOT = Path(__file__).resolve().parent
TEST_DB = TEST_ROOT / "test.db"
TEST_UPLOADS = TEST_ROOT / "uploads"

if TEST_DB.exists():
    TEST_DB.unlink()
TEST_UPLOADS.mkdir(parents=True, exist_ok=True)

os.environ["DATABASE_URL"] = f"sqlite:///{TEST_DB}"
os.environ["UPLOAD_DIR"] = str(TEST_UPLOADS)
os.environ["JWT_SECRET"] = "test-secret-key-with-enough-length"
os.environ["SEED_DEMO_DATA"] = "false"
os.environ["RATE_LIMIT_PER_MINUTE"] = "100000"
os.environ["LOGIN_RATE_LIMIT_PER_MINUTE"] = "100000"
os.environ["LIST_CACHE_SECONDS"] = "0"
os.environ["WEBHOOK_SECRET"] = "test-webhook-secret"

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture(scope="session")
def client():
    with TestClient(app) as test_client:
        yield test_client
