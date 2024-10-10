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
                d[pretty_field_names[k]] = f"{dur.days*24 + hours}:{minutes}:{seconds}"
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
