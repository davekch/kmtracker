from configparser import ConfigParser
from pathlib import Path
from datetime import datetime, timedelta
from collections import Counter
import sqlite3
import gpxpy
import os

from kmtracker.db import get_db_connection
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


def get_streaks(config: ConfigParser) -> Counter[datetime]:
    """
    get lengths of streaks of consecutive ride-days mapped to the end-date of the streaks
    {end_date: length_of_streak}
    """
    with get_db_connection(get_db_path(config)) as connection:
        timestamps = db.get_timestamps(connection)
    dates = []
    for stamp, in timestamps:
        date = datetime.fromisoformat(stamp).date()
        if date not in dates:
            # no duplicates
            dates.append(date)
    diffs = [(d1 - d2).days for d1, d2 in zip(dates, dates[1:])]
    streaks = Counter()
    on_streak = False
    current_streak_date = None
    for diff, date in zip(diffs + [0], dates):
        if diff == 1:
            if not on_streak:
                on_streak = True
                current_streak_date = date
            streaks[current_streak_date] += 1
        elif on_streak:
            # count one more because the diff is one shorter than the # of days
            streaks[current_streak_date] += 1
            on_streak = False
    return streaks


def get_summary(config: ConfigParser) -> dict:
    with get_db_connection(get_db_path(config)) as connection:
        d_tot = db.get_total_distance(connection)
        d_max, d_max_timestamp = db.get_max_distance_entry(connection)
        s_max_day, s_max_day_date = db.get_max_distance_by_day(connection)
        s_max, s_max_timestamp = db.get_max_speed_entry(connection)
        s_avg = db.get_average_speed(connection)
        n = db.get_total_rides(connection)
    streaks = get_streaks(config)
    longest_streaks = streaks.most_common(1)
    return {
        "distance_tot": d_tot,
        "distance_max": (d_max, d_max_timestamp),
        "distance_max_day": (s_max_day, s_max_day_date),
        "speed_max": (s_max, s_max_timestamp),
        "speed_mean": s_avg,
        "n_rides": n,
        "longest_streaks": longest_streaks,
    }
