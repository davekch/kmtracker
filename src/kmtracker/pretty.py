import sqlite3
from rich.console import Console
from rich.table import Table
from datetime import timedelta
import gpxpy
from functools import wraps

from kmtracker.db import Ride, Alias


console = Console()



def _format_duration(duration: timedelta) -> str:
    if not duration:
        return ""
    hours, remainder = divmod(duration.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{duration.days*24 + hours:02}:{minutes:02}:{seconds:02}"


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
        table.add_row(
            row.name,
            str(round(row.distance, 1)),
            _format_duration(row.duration),
            row.comment,
            str(row.segments),
        )
    console.print(table)


def print_rides(rows: list[Ride]):
    if not rows:
        print("Nothing to show.")
        return
    table = Table()
    table.add_column(Ride.columns.pk.value.display_name)
    table.add_column(Ride.columns.timestamp.value.display_name)
    table.add_column(Ride.columns.distance.value.display_name)
    table.add_column(Ride.columns.duration.value.display_name)
    table.add_column("Avg. speed (km/h)")
    table.add_column(Ride.columns.comment.value.display_name)
    table.add_column(Ride.columns.segments.value.display_name)
    table.add_column(Ride.columns.gpx.value.display_name)
    for row in rows:
        table.add_row(
            str(row.pk),
            row.timestamp.strftime("%Y-%m-%d"),
            str(round(row.distance, 1)),
            _format_duration(row.duration),
            str(round(row.speed, 1)) if row.speed else "",
            row.comment,
            str(row.segments),
            "✅" if row.gpx else "-"
        )
    console.print(table)


def print_summary(summary: dict):
    dist_max, dist_max_date = summary["distance_max"]
    dist_max_day, dist_max_day_date = summary["distance_max_day"]
    s_max, s_max_date = summary["speed_max"]
    streaks = summary["longest_streaks"]
    if not streaks:
        streaks_text = "-"
    else:
        n = streaks[0][1]
        streaks_text = f"{n} days (until {str(streaks[0][0])})"
    console.print(f"total distance           : [bold green]{round(summary['distance_tot'], 2)} km[/bold green] ({summary['n_rides']} rides)")
    console.print(f"longest ride             : {round(dist_max, 2)} km (on {dist_max_date.split('T')[0]})")
    console.print(f"maximum distance on a day: {round(dist_max_day, 2)} km (on {dist_max_day_date})")
    console.print(f"average speed            : {round(summary['speed_mean'], 1)} km/h")
    console.print(f"fastest ride             : {round(s_max, 1)} km/h (on {s_max_date.split('T')[0]})")
    console.print(f"longest streaks          : {streaks_text}")


def print_entry(ride: Ride):
    print_rides([ride])
    gpx_data = ride.gpx
    if gpx_data:
        gpx = gpxpy.parse(gpx_data)
        moving_data = gpx.get_moving_data()
        elevation = gpx.get_uphill_downhill()
        console.print(f"time in motion         : {_format_duration(timedelta(seconds=moving_data.moving_time))}")
        console.print(f"time at rest           : {_format_duration(timedelta(seconds=moving_data.stopped_time))}")
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
