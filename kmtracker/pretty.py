import sqlite3
from rich.console import Console
from rich.table import Table
from datetime import timedelta

from kmtracker.db import Rides


console = Console()


pretty_field_names = {
    "id": "ID",
    Rides.columns.distance: "Distance (km)",
    Rides.columns.timestamp: "Date",
    Rides.columns.duration: "Duration (hh:mm:ss)",
    Rides.columns.segments: "Segments",
    Rides.columns.comment: "Comment",
    "speed": "Avg. speed (km/h)",
    "has_gpx": "GPX",
}


def to_dict(row: sqlite3.Row) -> dict:
    """
    convert a row of the rides table to a nicely formatted dict
    """
    d = {}
    for k in row.keys():
        if k == Rides.columns.timestamp:
            d[pretty_field_names[k]] = row[k].split("T")[0]  # the date part of isoformat
        elif k == Rides.columns.duration:
            if not row[k]:
                d[pretty_field_names[k]] = ""
            else:
                dur = timedelta(seconds=row[k])
                hours, remainder = divmod(dur.seconds, 3600)
                minutes, seconds = divmod(remainder, 60)
                d[pretty_field_names[k]] = f"{dur.days*24 + hours:02}:{minutes:02}:{seconds:02}"
        elif isinstance(row[k], float):
            d[pretty_field_names[k]] = round(row[k], 1)
        elif k == "has_gpx":
            d[pretty_field_names[k]] = "✅" if row[k] else "-"
        else:
            d[pretty_field_names[k]] = row[k]
    return d


def print_rows(rows: list):
    if not rows:
        print("Nothing to show.")
        return
    table = Table()
    for col in rows[0].keys():
        table.add_column(pretty_field_names[col])
    for row in map(to_dict, rows):
        table.add_row(*[str(v or "") for v in row.values()])
    console.print(table)


def print_summary(summary: dict):
    dist_max, dist_max_date = summary["distance_max"]
    dist_max_day, dist_max_day_date = summary["distance_max_day"]
    s_max, s_max_date = summary["speed_max"]
    console.print(f"total distance           : [bold green]{round(summary['distance_tot'], 2)} km[/bold green] ({summary['n_rides']} rides)")
    console.print(f"longest ride             : {round(dist_max, 2)} km (on {dist_max_date.split('T')[0]})")
    console.print(f"maximum distance on a day: {round(dist_max_day, 2)} km (on {dist_max_day_date})")
    console.print(f"average speed            : {round(summary['speed_mean'], 1)} km/h")
    console.print(f"fastest ride             : {round(s_max, 1)} km/h (on {s_max_date.split('T')[0]})")
