"""Integration test fixtures.

These run against a real PostgreSQL instance: the schema uses ENUM, JSONB, and
IDENTITY columns, so a SQLite stand-in would test something other than what
ships. Set LOCALLEDGER_TEST_DSN to point at a scratch database.
"""

import os
from pathlib import Path

import pytest

TEST_DSN = os.environ.get("LOCALLEDGER_TEST_DSN")

# Configure settings before app modules import them.
os.environ.setdefault("DATABASE_URL", TEST_DSN or "postgresql+psycopg://localhost/none")
os.environ.setdefault("OLLAMA_VISION_MODEL", "test-vision-model")
os.environ.setdefault("WATCH_ENABLED", "false")

requires_db = pytest.mark.skipif(
    not TEST_DSN, reason="LOCALLEDGER_TEST_DSN is not set; skipping database tests"
)


@pytest.fixture
def settings(tmp_path: Path):
    from app.config import Settings

    return Settings(
        DATABASE_URL=TEST_DSN or "postgresql+psycopg://localhost/none",
        OLLAMA_VISION_MODEL="test-vision-model",
        DATA_ROOT=tmp_path,
        WATCH_ENABLED=False,
    )


@pytest.fixture
def session():
    """A session wrapped in a transaction that is always rolled back."""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import Session

    engine = create_engine(TEST_DSN, future=True)
    connection = engine.connect()
    transaction = connection.begin()
    db_session = Session(bind=connection, expire_on_commit=False)
    try:
        yield db_session
    finally:
        db_session.close()
        transaction.rollback()
        connection.close()
        engine.dispose()
