from datetime import datetime, timedelta
import pytest

from kmtracker import db


@pytest.fixture
def database():
    _db = db.Database(":memory:")
    try:
        _db.migrate()
        yield _db
    finally:
        _db.close()


def test_add(database):
    ride = db.Ride(
        database,
        distance=12,
        timestamp=datetime(2025, 8, 11, 10),
        duration=timedelta(minutes=37),
        comment="test",
        segments=1,
    )
    ride.save()
    fetched_ride = db.Ride.get_last_row(database)
    assert ride.timestamp == datetime(2025, 8, 11, 10) == fetched_ride.timestamp
    assert ride.distance == 12 == fetched_ride.distance
    assert ride.duration == timedelta(minutes=37) == fetched_ride.duration
    assert ride.comment == "test" == fetched_ride.comment
    assert ride.segments == 1 == fetched_ride.segments
    assert ride.gpx == None == fetched_ride.gpx


def test_update(database):
    ride = db.Ride(
        database,
        distance=12,
        timestamp=datetime(2025, 8, 11, 10),
        duration=timedelta(minutes=37),
        comment="test",
        segments=1,
    )
    ride.save()
    ride.distance = 12.5
    ride.save()
    fetched_ride = db.Ride.get_last_row(database)
    assert ride.distance == fetched_ride.distance == 12.5


def test_total_distance(database):
    db.Ride(database, timestamp=datetime.now(), distance=12).save()
    db.Ride(database, timestamp=datetime.now(), distance=3.4).save()
    assert db.Ride.get_total_distance(database) == 12 + 3.4
