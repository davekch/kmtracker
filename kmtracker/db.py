import sqlite3
from pathlib import Path
from contextlib import closing
from datetime import datetime
from datetime import timedelta


RIDE_TABLE = "rides"


def get_db_connection(path: Path):
    return closing(sqlite3.connect(path))


def create_db(path: Path):
    with get_db_connection(path) as connection:
        with closing(connection.cursor()) as cursor:
            cursor.execute(f"""
                CREATE TABLE {RIDE_TABLE} (
                    id INTEGER PRIMARY KEY,
                    distance_km REAL NOT NULL,
                    timestamp TEXT NOT NULL,
                    duration TEXT,
                    comment TEXT,
                    segments INTEGER DEFAULT 1 CHECK(segments > 0)
                )
            """)


def add_entry(
    connection: sqlite3.Connection,
    distance: float,
    timestamp: datetime,
    duration: timedelta,
    comment: str,
    segments: int,
):
    if duration is not None:
        hours, remainder = divmod(duration.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        duration_formatted = f"{hours}:{minutes}:{seconds}"
    else:
        duration_formatted = ""

    with closing(connection.cursor()) as cursor:
        cursor.execute(
            f"""INSERT INTO {RIDE_TABLE} (distance_km, timestamp, duration, comment, segments) VALUES (?, ?, ?, ?, ?)""",
            (
                distance,
                timestamp.isoformat(),
                duration_formatted,
                comment,
                segments
            )
        )
    connection.commit()
