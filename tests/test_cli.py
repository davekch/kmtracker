import pytest
import subprocess
from datetime import datetime, timedelta

from kmtracker import db


@pytest.fixture
def setup(tmp_path):
    path = tmp_path / "test.conf"
    with open(path, "w") as f:
        f.write(
            "[db]\n"
            f"path = {tmp_path}/test.sqlite3\n"
        )
    # prepare the db
    try:
        _db = db.Database(tmp_path / "test.sqlite3")
        _db.migrate()
        yield _db, ["kmtracker", "-f", str(path)]
    finally:
        _db.close()


def test_add(setup):
    _db, command = setup
    output = subprocess.check_output(
        command + ["add", "6.8", "-c", "test"]
    ).decode("utf-8")
    assert "Success" in output
    assert "6.8" in output
    assert "test" in output
    ride = db.Ride.get_last_row(_db)
    assert ride.distance == 6.8
    assert ride.comment == "test"


def test_amend(setup):
    _db, command = setup
    # populate the db
    db.Ride(_db, distance=78, timestamp=datetime(2025, 8, 23)).save()
    subprocess.call(
        command + ["amend", "-s", "2"]
    )
    ride = db.Ride.get_last_row(_db)
    assert ride.segments == 2
    assert ride.distance == 78


def test_alias_add(setup):
    _db, command = setup
    output = subprocess.check_output(
        command + ["alias", "add", "test", "-k", "34.2", "-s", "2", "-d", "1:21"]
    ).decode("utf-8")
    assert "new alias" in output
    alias = db.Alias.get_last_row(_db)
    assert alias.name == "test"
    assert alias.distance == 34.2
    assert alias.segments == 2
    assert alias.duration == timedelta(hours=1, minutes=21)


def test_alias_ls(setup):
    _db, command = setup
    alias = db.Alias(_db, name="test", distance=12.3)
    alias.save()
    output = subprocess.check_output(
        command + ["alias", "ls"]
    ).decode("utf-8")
    assert "test" in output
    assert "12.3" in output


def test_add_with_alias(setup):
    _db, command = setup
    alias = db.Alias(_db, name="test", distance=12.3, duration=timedelta(minutes=31))
    alias.save()
    # first test adding a ride by referencing the alias
    output = subprocess.check_output(
        command + ["add", "test"]
    ).decode("utf-8")
    assert "Success" in output
    ride = db.Ride.get_last_row(_db)
    assert ride.distance == 12.3
    assert ride.duration == timedelta(minutes=31)
    assert ride.comment is None
    assert ride.segments == 1

    # now test again but override some values
    subprocess.call(
        command + ["add", "test", "-d", "0:35", "-c", "test"]
    )
    ride = db.Ride.get_last_row(_db)
    assert ride.distance == 12.3
    assert ride.duration == timedelta(minutes=35)
    assert ride.comment == "test"
