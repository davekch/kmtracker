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
        gpx = "gpx"

    SELECT_ALL = (
        f"SELECT id, {columns.timestamp}, {columns.distance}, {columns.duration}, "
        f"{columns.distance} / {columns.duration} * 3600 AS speed, {columns.comment}, {columns.segments}, "
        f"CASE WHEN {columns.gpx} IS NULL THEN 0 ELSE 1 END AS has_gpx "
        f"FROM {name}"
    )


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
            # look up which migrations have already been performed
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
                print(f"performing migration '{module}'...")
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
    gpx: str,
):
    with closing(connection.cursor()) as cursor:
        cursor.execute(
            f"""INSERT INTO {Rides.name} (
                {Rides.columns.distance},
                {Rides.columns.timestamp},
                {Rides.columns.duration},
                {Rides.columns.comment},
                {Rides.columns.segments},
                {Rides.columns.gpx}
            ) VALUES (?, ?, ?, ?, ?, ?)""",
            (
                distance,
                timestamp.isoformat(),
                _to_seconds(duration),
                comment,
                segments,
                gpx
            )
        )
    connection.commit()


def amend(
    connection: sqlite3.Connection,
    id: int,
    distance: float,
    timestamp: datetime,
    duration: timedelta,
    comment: str,
    segments: int,
    gpx: str,
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
    if gpx:
        setters.append(f"{Rides.columns.gpx} = ?")
        values.append(gpx)
    if id is not None:
        where_clause = "id = ?"
        values.append(id)
    else:
        where_clause = f"id = (SELECT MAX(id) FROM {Rides.name})"
    command = f"""
        UPDATE {Rides.name} SET {', '.join(setters)}
        WHERE {where_clause}
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
            f"{Rides.SELECT_ALL} WHERE id=(SELECT MAX(id) FROM {Rides.name})"
        ).fetchone()


def get_entry(connection: sqlite3.Connection, id: int) -> sqlite3.Row:
    connection.row_factory = sqlite3.Row
    with closing(connection.cursor()) as cursor:
        return cursor.execute(
            f"{Rides.SELECT_ALL} WHERE id = ?",
            (id,)
        ).fetchone()


def get_latest_entries(connection: sqlite3.Connection, n: int) -> list[sqlite3.Row]:
    """
    return the latest n entries (by timestamp)
    """
    connection.row_factory = sqlite3.Row
    with closing(connection.cursor()) as cursor:
        return cursor.execute(
            f"{Rides.SELECT_ALL} ORDER BY {Rides.columns.timestamp} DESC LIMIT ?",
            (n,)
        ).fetchall()


def get_gpx(connection: sqlite3.Connection, id: int) -> str | None:
    with closing(connection.cursor()) as cursor:
        return cursor.execute(
            f"SELECT {Rides.columns.gpx} FROM {Rides.name} WHERE id = ?", (id,)
        ).fetchone()[0]


def get_total_distance(connection: sqlite3.Connection) -> float:
    with closing(connection.cursor()) as cursor:
        return cursor.execute(f"SELECT SUM({Rides.columns.distance}) FROM {Rides.name}").fetchone()[0]


def get_max_distance_entry(connection: sqlite3.Connection) -> tuple[int, str]:
    """get the maximum distance of a single ride with timestamp"""
    with closing(connection.cursor()) as cursor:
        return cursor.execute(
            f"SELECT MAX({Rides.columns.distance} / {Rides.columns.segments}) AS {Rides.columns.distance}, {Rides.columns.timestamp} "
            f"FROM {Rides.name}"
        ).fetchone()


def get_max_distance_by_day(connection: sqlite3.Connection) -> tuple[int, str]:
    """get the maximum distance covered on a day"""
    with closing(connection.cursor()) as cursor:
        return cursor.execute(f"""
            SELECT MAX(daily_distance), day
            FROM (
                SELECT DATE({Rides.columns.timestamp}) as day, SUM({Rides.columns.distance}) as daily_distance
                FROM {Rides.name}
                GROUP BY day
            )
        """).fetchone()


def get_max_speed_entry(connection: sqlite3.Connection) -> tuple[int, str]:
    """return the maximum speed with timestamp"""
    with closing(connection.cursor()) as cursor:
        return cursor.execute(
            f"SELECT MAX({Rides.columns.distance} / {Rides.columns.duration} * 3600) as speed, {Rides.columns.timestamp} "
            f"FROM {Rides.name} WHERE {Rides.columns.duration} IS NOT NULL"
        ).fetchone()


def get_average_speed(connection: sqlite3.Connection) -> float:
    """return the average speed of all entries with a duration in km/h"""
    with closing(connection.cursor()) as cursor:
        s_km, t_s = cursor.execute(
            f"SELECT SUM({Rides.columns.distance}), SUM({Rides.columns.duration}) "
            F"FROM {Rides.name} WHERE {Rides.columns.duration} IS NOT NULL"
        ).fetchone()
    return s_km / (t_s / 3600)


def get_total_rides(connection: sqlite3.Connection) -> int:
    with closing(connection.cursor()) as cursor:
        return cursor.execute(f"SELECT SUM({Rides.columns.segments}) FROM {Rides.name}").fetchone()[0]


def get_timestamps(connection: sqlite3.Connection) -> list:
    with closing(connection.cursor()) as cursor:
        return cursor.execute(
            f"SELECT {Rides.columns.timestamp} FROM {Rides.name} ORDER BY {Rides.columns.timestamp} DESC"
        ).fetchall()
