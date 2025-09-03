from configparser import ConfigParser
from contextlib import closing
from pathlib import Path
from datetime import datetime, timedelta
from collections import Counter
import sqlite3
import gpxpy
import os

from kmtracker import db


DEFAULT_CONFIG_PATH = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")) / "kmtracker.cfg"
DEFAULT_DB_PATH = "~/.kmtracker.sqlite3"


def get_config(path: Path=DEFAULT_CONFIG_PATH) -> ConfigParser:
    config = ConfigParser()
    if not path.exists():
        print("✨Welcome to kmtracker!✨\n")
        config["db"] = {
            "path": input(f"database file [{DEFAULT_DB_PATH}]: ") or DEFAULT_DB_PATH
        }
        with open(path, "w") as f:
            config.write(f)
            print(f"saved config to {path}")
    else:
        config.read(path)
    return config


def get_db_path(config: ConfigParser) -> Path:
    return Path(config["db"]["path"]).expanduser().resolve()


def get_database(config: ConfigParser) -> db.Database:
    return db.Database(get_db_path(config))


def add_alias(
    config: ConfigParser,
    name: str,
    distance: float=None,
    duration: timedelta=None,
    comment: str="",
    segments: int=1,
):
    with get_db_connection(get_db_path(config)) as connection:
        db.add_alias(connection, name, distance, duration, comment, segments)
        new = db.get_last_entry(connection, model=db.Alias)
    return new


def get_aliases(config: ConfigParser) -> list[sqlite3.Row]:
    with get_db_connection(get_db_path(config)) as connection:
        aliases = db.get_aliases(connection)
    return aliases


def from_gpx(config: ConfigParser, gpx_path: Path) -> list[sqlite3.Row]:
    """
    read and parse gpx_path and create new entries from its contents
    """
    with open(gpx_path) as f:
        gpx = gpxpy.parse(f)
    new = []
    for track in gpx.tracks:
        moving_data = track.get_moving_data()
        time_bounds = track.get_time_bounds()
        new.append(add(
            config=config,
            distance=moving_data.moving_distance / 1000,
            timestamp=time_bounds.start_time,
            duration=timedelta(seconds=moving_data.moving_time),
            comment=track.name,
            segments=len(track.segments),
            gpx_path=gpx_path,
        ))
    return new


def get_latest(config: ConfigParser, n: int) -> list[sqlite3.Row]:
    with get_db_connection(get_db_path(config)) as connection:
        latest = db.get_latest_entries(connection, n)
    return latest


def get_entry(config: ConfigParser, id: int) -> tuple[sqlite3.Row, str | None]:
    """
    get entry by ID. return row and gpx data separately
    """
    with get_db_connection(get_db_path(config)) as connection:
        return db.get_entry(connection, id), db.get_gpx(connection, id)

