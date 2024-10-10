import sqlite3
from pathlib import Path
from contextlib import closing
from datetime import datetime
from datetime import timedelta
import glob
import importlib


RIDE_TABLE = "rides"
MIGRATIONS_TABLE = "_migrations"


def get_db_connection(path: Path):
    return closing(sqlite3.connect(path))


def migrate(path: Path):
    """
    migrate changes to the database schema to the database
    or create a new one
    """
    # look up which migrations are available
    migration_modules = sorted(
        Path(m).stem for m in
        glob.glob(str(Path(__file__).parent / "_migrations" / "m*.py"))
    )
    with get_db_connection(path) as connection:
        with closing(connection.cursor()) as cursor:
            # look up which migrations have already performed
            try:
                migrations_performed = [
                    result[0] for result in
                    cursor.execute(f"SELECT name FROM {MIGRATIONS_TABLE}").fetchall()
                ]
            except sqlite3.OperationalError:
                migrations_performed = []

            # perform missing migrations
            for module in migration_modules:
                if module in migrations_performed:
                    continue
                migration = importlib.import_module(f"kmtracker._migrations.{module}")
                migration.run(cursor)
                # mark this migration as done
                cursor.execute(
                    f"INSERT INTO {MIGRATIONS_TABLE} (name) VALUES (?)",
                    (module,)
                )

        connection.commit()


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
    """
    return the last entry (highest ID)
    """
    connection.row_factory = sqlite3.Row
    with closing(connection.cursor()) as cursor:
        return cursor.execute(
            "SELECT id, timestamp, distance_km, duration, segments, comment "
            f"FROM {RIDE_TABLE} "
            f"WHERE id=(SELECT max(id) from {RIDE_TABLE})"
        ).fetchall()[0]


def get_latest_entries(connection: sqlite3.Connection, n: int) -> list[sqlite3.Row]:
    """
    return the latest n entries (by timestamp)
    """
    connection.row_factory = sqlite3.Row
    with closing(connection.cursor()) as cursor:
        latest = cursor.execute(
            "SELECT id, timestamp, distance_km, duration, segments, comment "
            f"FROM {RIDE_TABLE} "
            "ORDER BY timestamp DESC LIMIT ?",
            (n,)
        ).fetchall()
        return list(reversed(latest))
