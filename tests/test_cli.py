import pytest
import subprocess
from datetime import datetime

import kmtracker
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
        yield path, _db
    finally:
        _db.close()


def test_add(setup):
    config_path, _db = setup
    output = subprocess.check_output(
        ["kmtracker", "-f", str(config_path), "add", "6.8", "-c", "test"]
    ).decode("utf-8")
    assert "Success" in output
    assert "6.8" in output
    assert "test" in output
    ride = db.Ride.get_last_row(_db)
    assert ride.distance == 6.8
    assert ride.comment == "test"


def test_amend(setup):
    config_path, _db = setup
    # populate the db
    db.Ride(_db, distance=78, timestamp=datetime(2025, 8, 23)).save()
    subprocess.call(
        ["kmtracker", "-f", str(config_path), "amend", "-s", "2"]
    )
    ride = db.Ride.get_last_row(_db)
    assert ride.segments == 2
    assert ride.distance == 78
