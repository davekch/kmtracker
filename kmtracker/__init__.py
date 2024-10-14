from configparser import ConfigParser
from pathlib import Path
from datetime import datetime, timedelta
import sqlite3

from kmtracker.db import get_db_connection
from kmtracker import db


CONFIG_PATH = Path("~/.config/kmtracker.cfg").expanduser()
DEFAULT_DB_PATH = "~/.kmtracker.sqlite3"


def get_config() -> ConfigParser:
    config = ConfigParser()
    if not CONFIG_PATH.exists():
        print("✨Welcome to kmtracker!✨\n")
        config["db"] = {
            "path": input(f"database file [{DEFAULT_DB_PATH}]: ") or DEFAULT_DB_PATH
        }
        with open(CONFIG_PATH, "w") as f:
            config.write(f)
            print(f"saved config to {CONFIG_PATH}")
    else:
        config.read([CONFIG_PATH])
    return config


def get_db_path(config: ConfigParser) -> Path:
    return Path(config["db"]["path"]).expanduser().resolve()


def add(
    config: ConfigParser,
    distance: float,
    timestamp: datetime,
    duration: timedelta = None,
    comment: str = "",
    segments: int = 1,
    gpx_path: Path = None,
) -> sqlite3.Row:
    if gpx_path:
        with open(gpx_path) as f:
            gpx = f.read()  # we don't care at this point if it's really gpx; user's responsibility
    else:
        gpx = None
    with get_db_connection(get_db_path(config)) as connection:
        db.add_entry(connection, distance, timestamp, duration, comment, segments, gpx)
        new = db.get_last_entry(connection)
    return new


def amend(
    config: ConfigParser,
    id: int = None,
    distance: float = None,
    timestamp: datetime = None,
    duration: timedelta = None,
    comment: str = None,
    segments: int = None,
    gpx_path: Path = None,
) -> sqlite3.Row:
    if gpx_path:
        with open(gpx_path) as f:
            gpx = f.read()  # we don't care at this point if it's really gpx; user's responsibility
    else:
        gpx = None
    with get_db_connection(get_db_path(config)) as connection:
        db.amend(connection, id, distance, timestamp, duration, comment, segments, gpx)
        if not id:
            new = db.get_last_entry(connection)
        else:
            new = db.get_entry(connection, id)
    return new


def get_latest(config: ConfigParser, n: int) -> list[sqlite3.Row]:
    with get_db_connection(get_db_path(config)) as connection:
        latest = db.get_latest_entries(connection, n)
    return latest


def get_summary(config: ConfigParser) -> dict:
    with get_db_connection(get_db_path(config)) as connection:
        s_tot = db.get_total_distance(connection)
        s_max, s_max_timestamp = db.get_max_distance_entry(connection)
        s_max_day, s_max_day_date = db.get_max_distance_by_day(connection)
        s_max, s_max_timestamp = db.get_max_speed_entry(connection)
        s_avg = db.get_average_speed(connection)
        n = db.get_total_rides(connection)
    return {
        "distance_tot": s_tot,
        "distance_max": (s_max, s_max_timestamp),
        "distance_max_day": (s_max_day, s_max_day_date),
        "speed_max": (s_max, s_max_timestamp),
        "speed_mean": s_avg,
        "n_rides": n,
    }
