"""Test configuration and fixtures for Chirp API tests.

Creates an in-memory SQLite database using StaticPool for complete test isolation.
Enforces SQLite foreign key constraints via event listeners.
Provides a session fixture that creates fresh tables per test.
"""

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from chirp_api.db.models import Base


@pytest.fixture
def session(monkeypatch):
    """Create a fresh in-memory SQLite session with StaticPool for each test.

    Enforces foreign key constraints. All tables are created fresh per test.
    Also monkey-patches chirp_api.db.SessionLocal so handlers use the test DB.
    """
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    Base.metadata.create_all(engine)
    TestSession = sessionmaker(bind=engine, expire_on_commit=False)

    test_session = TestSession()

    # Monkey-patch SessionLocal so handlers use our test session
    import chirp_api.db as db_module

    monkeypatch.setattr(db_module, "SessionLocal", TestSession)

    try:
        yield test_session
    finally:
        test_session.close()
        Base.metadata.drop_all(engine)
        engine.dispose()
