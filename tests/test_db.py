from datetime import datetime, timedelta
import pytest
import sqlite3

from kmtracker import db


@pytest.fixture
def connection():
    conn = sqlite3.connect(":memory:")
    try:
        db.migrate(conn)
        yield conn
    finally:
        conn.close()


def test_add(connection):
    db.add_entry(
        connection=connection,
        distance=12,
        timestamp=datetime(2025, 8, 11, 10),
        duration=timedelta(minutes=37),
        comment="test",
        segments=1,
        gpx=""
    )
    row = db.get_last_entry(connection)
    assert row["timestamp"] == datetime(2025, 8, 11, 10).isoformat()
    assert row["distance_km"] == 12
    assert row["duration_s"] == 37*60
    assert row["comment"] == "test"
    assert row["segments"] == 1
