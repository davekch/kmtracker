import argparse
import dateutil
import sys
from datetime import datetime, timedelta
import dateutil.parser
from pathlib import Path

from kmtracker import db
from kmtracker import pretty
from kmtracker import (
    get_config,
    get_db_path,
    add,
    amend,
    from_gpx,
    get_latest,
    get_entry,
    get_summary,
    get_streaks,
)


def get_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)

    add = subparsers.add_parser("add", help="add a new ride")
    add.add_argument("distance", help="distance in km")
    add.add_argument("-t", "--timestamp", help="datetime of the ride")
    add.add_argument("-d", "--duration", help="duration of the ride")
    add.add_argument("-c", "--comment")
    add.add_argument("-s", "--segments", help="split this ride into n segments")
    add.add_argument("-g", "--gpx", help="add gpx file")

    amend = subparsers.add_parser("amend", help="change the latest entry")
    amend.add_argument("--id", help="ID of the entry to change. change the latest if omitted", type=int)
    amend.add_argument("-k", "--distance", help="distance in km")
    amend.add_argument("-t", "--timestamp", help="datetime of the ride")
    amend.add_argument("-d", "--duration", help="duration of the ride (hh:mm or hh:mm:ss)")
    amend.add_argument("-c", "--comment")
    amend.add_argument("-s", "--segments", help="split this ride into n segments")
    amend.add_argument("-g", "--gpx", help="add gpx file")

    loadgpx = subparsers.add_parser("loadgpx", help="add entries from a gpx file")
    loadgpx.add_argument("path", help="path to gpx file")

    ls = subparsers.add_parser("ls", help="show latest ride")
    ls.add_argument("-n", help="number of entries to show", type=int, default=-1)

    show = subparsers.add_parser("show", help="show details of an entry")
    show.add_argument("id", help="ID of the entry", type=int)

    stats = subparsers.add_parser("stats")

    args = parser.parse_args()
    return args


def parse_add_args(args: argparse.Namespace, auto_timestamp=True) -> dict:
    parsed = {}
    if args.distance:
        try:
            parsed["distance"] = float(args.distance)
        except ValueError:
            print(f"invalid float value for argument distance: {args.distance!r}")
            sys.exit(1)
    if args.timestamp:
        try:
            parsed["timestamp"] = dateutil.parser.parse(args.timestamp)
        except dateutil.parser.ParserError:
            print(f"invalid datetime for argument timestamp: {args.timestamp!r}")
            sys.exit(1)
    elif auto_timestamp:
        parsed["timestamp"] = datetime.now()
    if args.duration:
        try:
            # raises if the conversion to int fails or no case is matched
            match args.duration.split(":"):
                case [hours, minutes]:
                    parsed["duration"] = timedelta(hours=int(hours), minutes=int(minutes))
                case [hours, minutes, seconds]:
                    parsed["duration"] = timedelta(hours=int(hours), minutes=int(minutes), seconds=int(seconds))
                case _:
                    raise ValueError()
        except ValueError:
            print(f"invalid duration (must be hh:mm or hh:mm:ss): {args.duration!r}")
            sys.exit(1)
    if args.comment is not None:
        parsed["comment"] = args.comment
    if args.segments:
        try:
            parsed["segments"] = int(args.segments)
        except ValueError:
            print(f"invalid int value for argument segments: {args.segments!r}")
            sys.exit(1)
    if args.gpx:
        gpxpath = Path(args.gpx)
        if not gpxpath.exists():
            print(f"file not found: {args.gpx}")
            sys.exit(1)
        parsed["gpx_path"] = gpxpath
    return parsed


@pretty.pretty_errors
def main():
    args = get_args()
    config = get_config()
    db_path = get_db_path(config)

    if not db_path.exists():
        db.migrate(db_path)
        print(f"created a new DB at {db_path}")
    else:
        db.migrate(db_path)

    if args.command == "add":
        parsed_args = parse_add_args(args)
        new = add(config, **parsed_args)
        pretty.console.print("Success!✨ ", style="green bold", end="")
        pretty.console.print("Added a new ride:")
        pretty.print_rows([new])
        streaks = get_streaks(config)
        if (today := datetime.today().date()) in streaks:
            pretty.console.print(f"🚴[bold green]You're on a streak![/bold green] {streaks[today]} days in a row")
    elif args.command == "amend":
        parsed_args = parse_add_args(args, auto_timestamp=False)
        new = amend(config, id=args.id, **parsed_args)
        if args.id is None:
            pretty.console.print("Changed the latest entry:")
        else:
            pretty.console.print(f"Changed entry with ID {args.id}:")
        pretty.print_rows([new])
    elif args.command == "loadgpx":
        gpx_path = Path(args.path)
        if not gpx_path.exists():
            print(f"file not found: {args.path}")
        new = from_gpx(config, gpx_path)
        pretty.print_rows(new)
    elif args.command == "ls":
        latest = get_latest(config, args.n)
        pretty.print_rows(latest)
    elif args.command == "show":
        entry, gpx_data = get_entry(config, args.id)
        pretty.print_entry(entry, gpx_data)
    elif args.command == "stats":
        summary = get_summary(config)
        pretty.print_summary(summary)


if __name__ == "__main__":
    main()
