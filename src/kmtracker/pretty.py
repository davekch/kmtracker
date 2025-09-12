from rich.console import Console
from rich.table import Table
from datetime import timedelta
import gpxpy
from functools import wraps

from kmtracker.db import Ride, Alias
from kmtracker import db


console = Console()


def print_aliases(rows: list[Alias]):
    if not rows:
        print("Nothing to show.")
        return
    table = Table()
    table.add_column(Alias.columns.name.field.display_name)
    table.add_column(Alias.columns.distance.field.display_name)
    table.add_column(Alias.columns.duration.field.display_name)
    table.add_column(Alias.columns.comment.field.display_name)
    table.add_column(Alias.columns.segments.field.display_name)
    for row in rows:
        pretty = row.serialize_pretty()
        table.add_row(
            pretty["name"],
            pretty["distance"],
            pretty["duration"],
            pretty["comment"],
            pretty["segments"],
        )
    console.print(table)


def print_rides(rows: list[Ride]):
    if not rows:
        print("Nothing to show.")
        return
    table = Table()
    table.add_column(Ride.columns.pk.field.display_name)
    table.add_column(Ride.columns.timestamp.field.display_name)
    table.add_column(Ride.columns.distance.field.display_name)
    table.add_column(Ride.columns.duration.field.display_name)
    table.add_column("Avg. speed (km/h)")
    table.add_column(Ride.columns.comment.field.display_name)
    table.add_column(Ride.columns.segments.field.display_name)
    table.add_column(Ride.columns.gpx.field.display_name)
    for row in rows:
        pretty = row.serialize_pretty()
        table.add_row(
            pretty["pk"],
            pretty["timestamp"],
            pretty["distance"],
            pretty["duration"],
            db.FloatField.serialize_pretty(row.speed),
            pretty["comment"],
            pretty["segments"],
            "✅" if row.gpx else "-",
        )
    console.print(table)


def print_summary(summary: dict):
    streaks = summary["longest_streaks"]
    if not streaks:
        streaks_text = "-"
    else:
        n = streaks[0][1]
        streaks_text = f"{n} days (until {str(streaks[0][0])})"
    console.print(f"total distance           : [bold green]{summary['distance_tot']} km[/bold green] ({summary['n_rides']} rides)")
    console.print(f"longest ride             : {summary['distance_max']} km (on {summary['distance_max_date']})")
    console.print(f"maximum distance on a day: {summary['max_day_distance']} km (on {summary['max_day_date']})")
    console.print(f"average speed            : {summary['speed_mean']} km/h")
    console.print(f"fastest ride             : {summary['speed_max']} km/h (on {summary['speed_max_date']})")
    console.print(f"longest streaks          : {streaks_text}")


def print_entry(ride: Ride):
    print_rides([ride])
    gpx_data = ride.gpx
    if gpx_data:
        gpx = gpxpy.parse(gpx_data)
        moving_data = gpx.get_moving_data()
        elevation = gpx.get_uphill_downhill()
        console.print(f"time in motion         : {db.TimedeltaField.serialize_pretty(timedelta(seconds=moving_data.moving_time))}")
        console.print(f"time at rest           : {db.TimedeltaField.serialize_pretty(timedelta(seconds=moving_data.stopped_time))}")
        console.print(f"average speed in motion: {round(moving_data.moving_distance / moving_data.moving_time * 3.6, 1)} km/h")
        console.print(f"maximum speed          : {round(moving_data.max_speed * 3.6, 1)} km/h")
        console.print(f"uphill                 : {round(elevation.uphill, 0)} m")
        console.print(f"downhill               : {round(elevation.downhill, 0)} m")


def pretty_errors(f):
    error = "[bold red]error[/bold red]:"
    @wraps(f)
    def _f(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except PermissionError:
            console.print(f"{error} permission denied")
        except gpxpy.gpx.GPXXMLSyntaxException:
            console.print(f"{error} could not parse gpx file")
        except Exception as e:
            console.print(f"{error} {e}")
    return _f
