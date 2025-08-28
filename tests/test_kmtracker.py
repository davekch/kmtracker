from datetime import datetime, timedelta
import pytest

import kmtracker
from kmtracker import db


@pytest.fixture
def config(tmp_path):
    db_path = tmp_path / "test.sqlite3"
    with db.get_db_connection(db_path) as connection:
        db.migrate(connection)
    return {"db": {"path": db_path}}


def test_add(config):
    new = kmtracker.add(
        config=config,
        distance=12.3,
        timestamp=datetime(2025, 8, 22, 10, 1),
        segments=2,
    )
    assert new["distance_km"] == 12.3
    assert new["timestamp"] == datetime(2025, 8, 22, 10, 1).isoformat()
    assert new["duration_s"] == None
    assert new["speed"] == None
    assert new["comment"] == ""
    assert new["segments"] == 2
    assert new["has_gpx"] == False


def test_amend(config):
    new = kmtracker.add(
        config=config,
        distance=12.3,
        timestamp=datetime(2025, 8, 22, 10, 1),
    )
    # add segments
    new = kmtracker.amend(config, segments=2)
    assert new["distance_km"] == 12.3
    assert new["timestamp"] == datetime(2025, 8, 22, 10, 1).isoformat()
    assert new["duration_s"] == None
    assert new["speed"] == None
    assert new["comment"] == ""
    assert new["segments"] == 2
    assert new["has_gpx"] == False
