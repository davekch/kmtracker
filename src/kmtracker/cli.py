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
    add_alias,
    from_gpx,
    get_latest,
    get_entry,
    get_summary,
    get_streaks,
)


def get_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("-f", "--config", help="path to config file", type=Path)
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

    alias = subparsers.add_parser("alias", help="save default values for a ride under a name")
    alias.add_argument("name")
    alias.add_argument("-k", "--distance", help="default value for distance in km")
    alias.add_argument("-d", "--duration", help="default value for duration of the ride")
    alias.add_argument("-c", "--comment", help="default value for comment")
    alias.add_argument("-s", "--segments", help="default value for number of segments")

    loadgpx = subparsers.add_parser("loadgpx", help="add entries from a gpx file")
    loadgpx.add_argument("path", help="path to gpx file")

    ls = subparsers.add_parser("ls", help="show latest ride")
    ls.add_argument("-n", help="number of entries to show", type=int, default=-1)

    show = subparsers.add_parser("show", help="show details of an entry")
    show.add_argument("id", help="ID of the entry", type=int)

    stats = subparsers.add_parser("stats")

    args = parser.parse_args()
    return args


def convert_common_flags(args: argparse.Namespace, auto_timestamp=True) -> dict:
    """
    takes an argparse Namespace and parses and converts flags that are common across multiple
    commands (add, alias, amend) like distance, timestamp, etc
    """
    parsed = {}
    if hasattr(args, "distance") and args.distance:
        try:
            parsed["distance"] = float(args.distance)
        except ValueError:
            print(f"invalid float value for argument distance: {args.distance!r}")
            sys.exit(1)
    if hasattr(args, "timestamp") and args.timestamp:
        try:
            parsed["timestamp"] = dateutil.parser.parse(args.timestamp)
        except dateutil.parser.ParserError:
            print(f"invalid datetime for argument timestamp: {args.timestamp!r}")
            sys.exit(1)
    elif auto_timestamp:
        parsed["timestamp"] = datetime.now()
    if hasattr(args, "duration") and args.duration:
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
    if hasattr(args, "comment") and args.comment is not None:
        parsed["comment"] = args.comment
    if hasattr(args, "segments") and args.segments:
        try:
            parsed["segments"] = int(args.segments)
        except ValueError:
            print(f"invalid int value for argument segments: {args.segments!r}")
            sys.exit(1)
    if hasattr(args, "gpx") and args.gpx:
        gpxpath = Path(args.gpx)
        if not gpxpath.exists():
            print(f"file not found: {args.gpx}")
            sys.exit(1)
        parsed["gpx_path"] = gpxpath
    return parsed


@pretty.pretty_errors
def main():
    args = get_args()
    if args.config:
        config = get_config(args.config)
    else:
        config = get_config()
    db_path = get_db_path(config)

    if not db_path.exists():
        with db.get_db_connection(db_path) as connection:
            db.migrate(connection)
        print(f"created a new DB at {db_path}")
    else:
        with db.get_db_connection(db_path) as connection:
            db.migrate(connection)

    if args.command == "add":
        parsed_args = convert_common_flags(args)
        new = add(config, **parsed_args)
        pretty.console.print("Success!✨ ", style="green bold", end="")
        pretty.console.print("Added a new ride:")
        pretty.print_rows([new])
        streaks = get_streaks(config)
        if (today := datetime.today().date()) in streaks:
            pretty.console.print(f"🚴[bold green]You're on a streak![/bold green] {streaks[today]} days in a row")
    elif args.command == "amend":
        parsed_args = convert_common_flags(args, auto_timestamp=False)
        new = amend(config, id=args.id, **parsed_args)
        if args.id is None:
            pretty.console.print("Changed the latest entry:")
        else:
            pretty.console.print(f"Changed entry with ID {args.id}:")
        pretty.print_rows([new])
    elif args.command == "alias":
        parsed_args = convert_common_flags(args, auto_timestamp=False)
        new = add_alias(config, args.name, **parsed_args)
        pretty.console.print(f"Added a new alias with name {args.name}:")
        pretty.print_rows([new])
    elif args.command == "loadgpx":
        gpx_path = Path(args.path)
        if not gpx_path.exists():
            print(f"file not found: {args.path}")
        new = from_gpx(config, gpx_path)
        pretty.print_rows(new)
        streaks = get_streaks(config)
        if (today := datetime.today().date()) in streaks:
            pretty.console.print(f"🚴[bold green]You're on a streak![/bold green] {streaks[today]} days in a row")
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
