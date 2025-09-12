import sqlite3
from pathlib import Path
from contextlib import closing
from collections import Counter
from datetime import datetime
from datetime import timedelta
from enum import Enum
import gpxpy
import glob
import importlib
from typing import Self


class Database:
    def __init__(self, path: str):
        # you need to make sure that every command / request gets its own
        # db connection, then it's fine to have check_same_thread=False
        self.connection = sqlite3.connect(path, check_same_thread=False)
        self.connection.row_factory = sqlite3.Row

    def close(self):
        self.connection.close()

    def cursor(self) -> sqlite3.Cursor:
        return self.connection.cursor()

    def commit(self):
        self.connection.commit()

    def migrate(self):
        """
        migrate changes to the database schema to the database
        or create a new one
        """
        # look up which migrations are available
        migration_modules = sorted(
            Path(m).stem for m in
            glob.glob(str(Path(__file__).parent / "_migrations" / "m*.py"))
        )
        with closing(self.connection.cursor()) as cursor:
            # look up which migrations have already been performed
            try:
                migrations_performed = [
                    result[0] for result in
                    cursor.execute(f"SELECT {Migrations.columns.name} FROM {Migrations.table}").fetchall()
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
                    f"INSERT INTO {Migrations.table} ({Migrations.columns.name}) VALUES (?)",
                    (module,)
                )
        self.commit()


class Field:
    def __init__(self, column_name: str, display_name: str=None):
        self.name = column_name
        self.display_name = display_name or column_name

    @staticmethod
    def parse(value):
        return value

    @staticmethod
    def serialize(value):
        return value

    @staticmethod
    def serialize_pretty(value) -> str:
        if value is None:
            return ""
        return str(value)


class DatetimeField(Field):
    @staticmethod
    def parse(value: str):
        if value:
            return datetime.fromisoformat(value)

    @staticmethod
    def serialize(value: datetime) -> str:
        if value:
            return value.isoformat()

    @staticmethod
    def serialize_pretty(value: datetime):
        return value.strftime("%Y-%m-%d")


class TimedeltaField(Field):
    @staticmethod
    def parse(value: int):
        if value:
            return timedelta(seconds=value)

    @staticmethod
    def serialize(value: timedelta) -> int:
        if value:
            return value.total_seconds()

    @staticmethod
    def serialize_pretty(value: timedelta):
        if value is None:
            return ""
        hours, remainder = divmod(value.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{value.days*24 + hours:02}:{minutes:02}:{seconds:02}"


class FloatField(Field):
    @staticmethod
    def serialize_pretty(value):
        if value is None:
            return ""
        return str(round(value, 1))


class ColumnEnum(Enum):
    """
    enumeration of fields
    """

    @property
    def field(self) -> Field:
        return self.value

    @property
    def column_name(self) -> str:
        return self.field.name

    def __str__(self):
        return str(self.column_name)


class Model:
    """
    represents a table in the database. `columns` is an enumeration of `Field`s
    """
    table: str

    class columns(ColumnEnum):
        ...

    def __init_subclass__(cls):
        if not issubclass(cls.columns, ColumnEnum):
            raise TypeError(f"{cls.__name__}.columns must inherit ColumnEntry")
        for column in cls.columns:
            if not isinstance(column.field, Field):
                raise TypeError(f"members of columns must be of type Field: {cls.__name__}.columns.{column.name} is {type(column.field)}")

    def __init__(self, db: Database, **kwargs):
        self._db = db
        for column in self.columns:
            setattr(
                self,
                column.name,
                kwargs.pop(column.name, None),
            )
        if kwargs:
            raise TypeError(f"{kwargs.keys()} are invalid keyword arguments for {self.__class__.__name__}")

    @classmethod
    def from_row(cls, db: Database, row: sqlite3.Row):
        attrs = {column.name: column.field.parse(row[column.column_name]) for column in cls.columns}
        return cls(
            db,
            **attrs
        )

    def serialize(self) -> dict:
        return {
            column.name: column.field.serialize(getattr(self, column.name))
            for column in self.columns
        }

    def serialize_pretty(self) -> dict:
        return {
            column.name: column.field.serialize_pretty(getattr(self, column.name))
            for column in self.columns
        }

    def save(self):
        """
        write the current object to the db, updating fields if self.pk is not None
        and adding a new row otherwise
        """
        if not self.pk:
            # add a new row
            attrs = {column.name: getattr(self, column.name) for column in self.columns}
            attrs.pop("pk")
            self.add_row(self._db, **attrs)
            new = self.get_last_row(self._db) # get the row we just created
            self.pk = new.pk
        else:
            # update existing row
            setters = ", ".join(
                f"{column.column_name} = ?"
                for column in self.columns if column.column_name != "id"
            )
            values = [
                column.field.serialize(getattr(self, column.name))
                for column in self.columns if column.column_name != "id"
            ]
            with closing(self._db.cursor()) as cursor:
                cursor.execute(
                    f"UPDATE {self.table} SET {setters} WHERE id = ?",
                    (*values, self.pk)
                )
            self._db.commit()

    @classmethod
    def select_all_query(cls) -> str:
        return f"SELECT {', '.join(str(column) for column in cls.columns)} FROM {cls.table}"

    @classmethod
    def add_row(cls, db: Database, **kwargs):
        """insert a new row into the table. takes values for columns as keyword arguments"""
        with closing(db.cursor()) as cursor:
            cursor.execute(
                f"""INSERT INTO {cls.table} (
                    {', '.join(str(col) for col in cls.columns)}
                ) VALUES ({', '.join('?' for _ in range(len(cls.columns)))})
                """,
                tuple(col.field.serialize(kwargs.get(col.name)) for col in cls.columns)
            )
        db.commit()

    @classmethod
    def get_last_row(cls, db: Database) -> Self:
        """
        return the last entry (highest ID)
        """
        with closing(db.cursor()) as cursor:
            row = cursor.execute(
                f"{cls.select_all_query()} WHERE id=(SELECT MAX(id) FROM {cls.table})"
            ).fetchone()
        return cls.from_row(db, row)

    @classmethod
    def get_row(cls, db: Database, id: int) -> Self:
        with closing(db.cursor()) as cursor:
            row = cursor.execute(
                f"{cls.select_all_query()} WHERE id = ?",
                (id,)
            ).fetchone()
        if not row:
            raise KeyError(f"no entry with ID {id}")
        return cls.from_row(db, row)


class Ride(Model):
    table = "rides"

    class columns(ColumnEnum):
        pk = Field("id", display_name="ID")
        distance = FloatField("distance_km", display_name="Distance (km)")
        timestamp = DatetimeField("timestamp", display_name="Date")
        duration = TimedeltaField("duration_s", display_name="Duration (hh:mm:ss)")
        comment = Field("comment", display_name="Comment")
        segments = Field("segments", display_name="Segments")
        gpx = Field("gpx", display_name="GPX")

    @property
    def has_gpx(self) -> bool:
        return bool(self.gpx)

    @property
    def speed(self) -> int:
        if self.distance and self.duration:
            return self.distance / self.duration.total_seconds() * 3600

    @classmethod
    def get_latest_entries(cls, db: Database, n: int) -> list[Self]:
        """
        return the latest n entries (by timestamp)
        """
        with closing(db.cursor()) as cursor:
            rows = cursor.execute(
                f"{cls.select_all_query()} ORDER BY {cls.columns.timestamp} DESC LIMIT ?",
                (n,)
            ).fetchall()
        return [cls.from_row(db, row) for row in rows]

    @classmethod
    def get_total_distance(cls, db: Database) -> float:
        with closing(db.cursor()) as cursor:
            return cursor.execute(f"SELECT SUM({cls.columns.distance}) FROM {cls.table}").fetchone()[0]

    @classmethod
    def get_max_distance_entry(cls, db: Database) -> tuple[int, str]:
        """get the maximum distance of a single ride with timestamp"""
        with closing(db.cursor()) as cursor:
            return cursor.execute(
                f"SELECT MAX({cls.columns.distance} / {cls.columns.segments}) AS {cls.columns.distance}, {cls.columns.timestamp} "
                f"FROM {cls.table}"
            ).fetchone()

    @classmethod
    def get_max_distance_by_day(cls, db: Database) -> tuple[int, str]:
        """get the maximum distance covered on a day"""
        with closing(db.cursor()) as cursor:
            return cursor.execute(f"""
                SELECT MAX(daily_distance), day
                FROM (
                    SELECT DATE({Ride.columns.timestamp}) as day, SUM({Ride.columns.distance}) as daily_distance
                    FROM {Ride.table}
                    GROUP BY day
                )
            """).fetchone()

    @classmethod
    def get_max_speed_entry(cls, db: Database) -> tuple[int, str]:
        """return the maximum speed with timestamp"""
        with closing(db.cursor()) as cursor:
            return cursor.execute(
                f"SELECT MAX({cls.columns.distance} / {cls.columns.duration} * 3600) as speed, {cls.columns.timestamp} "
                f"FROM {cls.table} WHERE {cls.columns.duration} IS NOT NULL"
            ).fetchone()

    @classmethod
    def get_average_speed(cls, db: Database) -> float:
        """return the average speed of all entries with a duration in km/h"""
        with closing(db.cursor()) as cursor:
            s_km, t_s = cursor.execute(
                f"SELECT SUM({cls.columns.distance}), SUM({cls.columns.duration}) "
                F"FROM {cls.table} WHERE {cls.columns.duration} IS NOT NULL"
            ).fetchone()
        if t_s is None:
            raise ValueError("no entries in database")
        return s_km / (t_s / 3600)

    @classmethod
    def get_total_rides(cls, db: Database) -> int:
        with closing(db.cursor()) as cursor:
            return cursor.execute(f"SELECT SUM({cls.columns.segments}) FROM {cls.table}").fetchone()[0]

    @classmethod
    def get_timestamps(cls, db: Database) -> list[datetime]:
        with closing(db.cursor()) as cursor:
            stamps = cursor.execute(
                f"SELECT {cls.columns.timestamp} FROM {cls.table} ORDER BY {cls.columns.timestamp} DESC"
            ).fetchall()
        return [cls.columns.timestamp.field.parse(s) for s, in stamps]

    @classmethod
    def get_streaks(cls, db: Database) -> Counter[datetime]:
        """
        get lengths of streaks of consecutive ride-days mapped to the end-date of the streaks
        {end_date: length_of_streak}
        """
        timestamps = cls.get_timestamps(db)
        dates = []
        for stamp in timestamps:
            date = stamp.date()
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

    @classmethod
    def get_summary(cls, db: Database) -> dict:
        d_tot = cls.get_total_distance(db)
        d_max, d_max_timestamp = cls.get_max_distance_entry(db)
        s_max_day, s_max_day_date = cls.get_max_distance_by_day(db)
        s_max, s_max_timestamp = cls.get_max_speed_entry(db)
        s_avg = cls.get_average_speed(db)
        n = cls.get_total_rides(db)
        streaks = cls.get_streaks(db)
        longest_streaks = streaks.most_common(1)
        return {
            "distance_tot": round(d_tot, 2),
            "distance_max": round(d_max, 2),
            "distance_max_date": d_max_timestamp.split("T")[0],
            "max_day_distance": round(s_max_day, 2),
            "max_day_date": s_max_day_date.split("T")[0],
            "speed_max": round(s_max, 1),
            "speed_max_date": s_max_timestamp.split("T")[0],
            "speed_mean": round(s_avg, 1),
            "n_rides": n,
            "longest_streaks": longest_streaks,
        }

    @classmethod
    def from_gpx(cls, db: Database, gpx_path: Path) -> list[Self]:
        """
        read and parse gpx_path and create new entries from its contents
        """
        with open(gpx_path) as f:
            raw_gpx = f.read()
            gpx = gpxpy.parse(raw_gpx)
        new = []
        for track in gpx.tracks:
            moving_data = track.get_moving_data()
            time_bounds = track.get_time_bounds()
            ride = cls(
                db=db,
                distance=moving_data.moving_distance / 1000,
                timestamp=time_bounds.start_time,
                duration=timedelta(seconds=moving_data.moving_time),
                comment=track.name,
                segments=len(track.segments),
                gpx=raw_gpx,
            )
            ride.save()
            new.append(ride)
        return new


class Alias(Model):
    """
    represents a table of default values for rides
    """
    table = "aliases"
    
    class columns(ColumnEnum):
        pk = Field("id", display_name="ID")
        name = Field("name", display_name="Name")
        distance = FloatField("distance_km", display_name="Distance (km)")
        duration = TimedeltaField("duration_s", display_name="Duration (hh:mm:ss)")
        comment = Field("comment", display_name="Comment")
        segments = Field("segments", display_name="Segments")

    @classmethod
    def get_all(cls, db: Database) -> list[Self]:
        with closing(db.cursor()) as cursor:
            rows = cursor.execute(
                f"{cls.select_all_query()} ORDER BY {cls.columns.name} DESC"
            ).fetchall()
        return [cls.from_row(db, row) for row in rows]

    @classmethod
    def get_by_name(cls, db: Database, name: str) -> Self:
        with closing(db.cursor()) as cursor:
            row = cursor.execute(
                f"{cls.select_all_query()} WHERE name = ?",
                (name,)
            ).fetchone()
        if not row:
            raise KeyError(f"no alias with name {name}")
        return cls.from_row(db, row)


class Migrations(Model):
    table = "_migrations"

    class columns(ColumnEnum):
        name = Field("name")
        timestamp = DatetimeField("timestamp")
