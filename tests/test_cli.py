import pytest
import subprocess

import kmtracker
from kmtracker import db


@pytest.fixture
def config_path(tmp_path):
    path = tmp_path / "test.conf"
    with open(path, "w") as f:
        f.write(
            "[db]\n"
            f"path = {tmp_path}/test.sqlite3\n"
        )
    # prepare the db
    db.Database(tmp_path / "test.sqlite3").migrate()
    return path


def test_add(config_path):
    output = subprocess.check_output(
        ["kmtracker", "-f", str(config_path), "add", "6.8", "-c", "test"]
    ).decode("utf-8")
    assert "Success" in output
    assert "6.8" in output
    assert "test" in output
