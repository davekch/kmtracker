import sqlite3
from pathlib import Path
from contextlib import closing
from datetime import datetime
from datetime import timedelta
import glob
import importlib


# constants of table and column names
class Rides:
    name = "rides"

    class columns:
        distance = "distance_km"
        timestamp = "timestamp"
        duration = "duration_s"
        comment = "comment"
        segments = "segments"


class Migrations:
    name = "_migrations"

    class columns:
        name = "name"
        timestamp = "timestamp"


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
                    cursor.execute(f"SELECT {Migrations.columns.name} FROM {Migrations.name}").fetchall()
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
                    f"INSERT INTO {Migrations.name} ({Migrations.columns.name}) VALUES (?)",
                    (module,)
                )

        connection.commit()


def _to_seconds(duration: timedelta) -> int:
    if duration is not None:
        return duration.days * 60 * 60 * 24 + duration.seconds
    else:
        return None


def add_entry(
    connection: sqlite3.Connection,
    distance: float,
    timestamp: datetime,
    duration: timedelta,
    comment: str,
    segments: int,
):
    with closing(connection.cursor()) as cursor:
        cursor.execute(
            f"""INSERT INTO {Rides.name} (
                {Rides.columns.distance},
                {Rides.columns.timestamp},
                {Rides.columns.duration},
                {Rides.columns.comment},
                {Rides.columns.segments}
            ) VALUES (?, ?, ?, ?, ?)""",
            (
                distance,
                timestamp.isoformat(),
                _to_seconds(duration),
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
        setters.append(f"{Rides.columns.distance} = ?")
        values.append(distance)
    if timestamp:
        setters.append(f"{Rides.columns.timestamp} = ?")
        values.append(timestamp.isoformat())
    if duration:
        setters.append(f"{Rides.columns.duration} = ?")
        values.append(_to_seconds(duration))
    if comment is not None:
        # might be empty string
        setters.append(f"{Rides.columns.comment} = ?")
        values.append(comment)
    if segments:
        setters.append(f"{Rides.columns.segments} = ?")
        values.append(segments)
    command = f"""
        UPDATE {Rides.name} SET {', '.join(setters)}
        WHERE id=(SELECT max(id) FROM {Rides.name})
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
            f"SELECT id, {Rides.columns.timestamp}, {Rides.columns.distance}, {Rides.columns.duration}, {Rides.columns.comment}, {Rides.columns.segments} "
            f"FROM {Rides.name} "
            f"WHERE id=(SELECT max(id) from {Rides.name})"
        ).fetchall()[0]


def get_latest_entries(connection: sqlite3.Connection, n: int) -> list[sqlite3.Row]:
    """
    return the latest n entries (by timestamp)
    """
    connection.row_factory = sqlite3.Row
    with closing(connection.cursor()) as cursor:
        latest = cursor.execute(
            f"SELECT id, {Rides.columns.timestamp}, {Rides.columns.distance}, {Rides.columns.duration}, {Rides.columns.comment}, {Rides.columns.segments} "
            f"FROM {Rides.name} "
            f"ORDER BY {Rides.columns.timestamp} DESC LIMIT ?",
            (n,)
        ).fetchall()
        return list(reversed(latest))
