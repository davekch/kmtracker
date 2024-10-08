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


def _format_duration(duration: timedelta) -> str:
    if duration is not None:
        hours, remainder = divmod(duration.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{hours}:{minutes}:{seconds}"
    else:
        return ""


def add_entry(
    connection: sqlite3.Connection,
    distance: float,
    timestamp: datetime,
    duration: timedelta,
    comment: str,
    segments: int,
):
    duration_formatted = _format_duration(duration)

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


def amend(
    connection: sqlite3.Connection,
    distance: float,
    timestamp: datetime,
    duration: timedelta,
    comment: str,
    segments: int,
):
    """
    change the latest entry with the given values
    """
    setters = []
    values = []
    # build setters and values such that they can be safely inserted into cursor.execute
    if distance:
        setters.append("distance_km = ?")
        values.append(distance)
    if timestamp:
        setters.append("timestamp = ?")
        values.append(timestamp.isoformat())
    if duration:
        setters.append("duration = ?")
        values.append(_format_duration(duration))
    if comment is not None:
        # might be empty string
        setters.append("comment = ?")
        values.append(comment)
    if segments:
        setters.append("segments = ?")
        values.append(segments)
    command = f"""
        UPDATE {RIDE_TABLE} SET {', '.join(setters)}
        WHERE id=(SELECT max(id) FROM {RIDE_TABLE})
    """
    with closing(connection.cursor()) as cursor:
        cursor.execute(command, tuple(values))
    connection.commit()


def get_last_entry(connection: sqlite3.Connection) -> sqlite3.Row:
    connection.row_factory = sqlite3.Row
    with closing(connection.cursor()) as cursor:
        return cursor.execute(
            "SELECT id, timestamp, distance_km, duration, segments, comment "
            f"FROM {RIDE_TABLE} "
            f"WHERE id=(SELECT max(id) from {RIDE_TABLE})"
        ).fetchall()[0]
