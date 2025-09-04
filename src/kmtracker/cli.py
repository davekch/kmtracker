import argparse
import dateutil
import sys
from configparser import ConfigParser
from contextlib import closing
from datetime import datetime, timedelta
import dateutil.parser
from pathlib import Path

from kmtracker.db import Database, Ride, Alias
from kmtracker import pretty
from kmtracker import (
    get_config,
    get_db_path,
    get_database,
)


def cli_add(database: Database, args: argparse.Namespace):
    parsed_args = convert_common_flags(args)
    Ride(database, **parsed_args).save()
    new = Ride.get_last_row(database)
    pretty.console.print("Success!✨ ", style="green bold", end="")
    pretty.console.print("Added a new ride:")
    pretty.print_rides([new])
    streaks = Ride.get_streaks(database)
    if (today := datetime.today().date()) in streaks:
        pretty.console.print(f"🚴[bold green]You're on a streak![/bold green] {streaks[today]} days in a row")


def cli_amend(database: Database, args: argparse.Namespace):
    parsed_args = convert_common_flags(args, auto_timestamp=False)
    if args.id is None:
        pretty.console.print("Changed the latest entry:")
        ride = Ride.get_last_row(database)
    else:
        pretty.console.print(f"Changed entry with ID {args.id}:")
        ride = Ride.get_row(args.id)
    for field, value in parsed_args.items():
        setattr(ride, field, value)
    ride.save()
    pretty.print_rides([ride])


def cli_alias_add(db: Database, args: argparse.Namespace):
    parsed_args = convert_common_flags(args, auto_timestamp=False)
    new = Alias(db, name=args.name, **parsed_args)
    new.save()
    pretty.console.print(f"Added a new alias with name {args.name}:")
    pretty.print_aliases([new])


def cli_alias_ls(db: Database, args: argparse.Namespace):
    aliases = Alias.get_all(db)
    pretty.print_aliases(aliases)


def cli_loadgpx(db: Database, args: argparse.Namespace):
    gpx_path = Path(args.path)
    if not gpx_path.exists():
        print(f"file not found: {args.path}")
    new = Ride.from_gpx(db, gpx_path)
    pretty.print_rides(new)
    streaks = Ride.get_streaks(db)
    if (today := datetime.today().date()) in streaks:
        pretty.console.print(f"🚴[bold green]You're on a streak![/bold green] {streaks[today]} days in a row")


def cli_ls(db: Database, args: argparse.Namespace):
    latest = Ride.get_latest_entries(db, args.n)
    pretty.print_rides(latest)


def cli_show(db: Database, args: argparse.Namespace):
    ride = Ride.get_row(db, args.id)
    pretty.print_entry(ride)


def cli_stats(db: Database, args: argparse.Namespace):
    summary = Ride.get_summary(db)
    pretty.print_summary(summary)


def get_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("-f", "--config", help="path to config file", type=Path)
    subparsers = parser.add_subparsers(dest="command", required=True)

    add = subparsers.add_parser("add", help="add a new ride")
    add.add_argument("distance", help="distance in km or name of alias")
    add.add_argument("-t", "--timestamp", help="datetime of the ride")
    add.add_argument("-d", "--duration", help="duration of the ride")
    add.add_argument("-c", "--comment")
    add.add_argument("-s", "--segments", help="split this ride into n segments", type=int, default=1)
    add.add_argument("-g", "--gpx", help="add gpx file")
    add.set_defaults(func=cli_add)

    amend = subparsers.add_parser("amend", help="change the latest entry")
    amend.add_argument("--id", help="ID of the entry to change. change the latest if omitted", type=int)
    amend.add_argument("-k", "--distance", help="distance in km")
    amend.add_argument("-t", "--timestamp", help="datetime of the ride")
    amend.add_argument("-d", "--duration", help="duration of the ride (hh:mm or hh:mm:ss)")
    amend.add_argument("-c", "--comment")
    amend.add_argument("-s", "--segments", help="split this ride into n segments")
    amend.add_argument("-g", "--gpx", help="add gpx file")
    amend.set_defaults(func=cli_amend)

    alias = subparsers.add_parser("alias", help="manage default values for rides")
    alias_subparsers = alias.add_subparsers(dest="command", required=True)
    alias_add = alias_subparsers.add_parser("add", help="add an alias")
    alias_add.add_argument("name")
    alias_add.add_argument("-k", "--distance", help="default value for distance in km")
    alias_add.add_argument("-d", "--duration", help="default value for duration of the ride")
    alias_add.add_argument("-c", "--comment", help="default value for comment")
    alias_add.add_argument("-s", "--segments", help="default value for number of segments", type=int, default=1)
    alias_add.set_defaults(func=cli_alias_add)
    alias_ls = alias_subparsers.add_parser("ls", help="list all aliases")
    alias_ls.set_defaults(func=cli_alias_ls)

    loadgpx = subparsers.add_parser("loadgpx", help="add entries from a gpx file")
    loadgpx.add_argument("path", help="path to gpx file")
    loadgpx.set_defaults(func=cli_loadgpx)

    ls = subparsers.add_parser("ls", help="show latest ride")
    ls.add_argument("-n", help="number of entries to show", type=int, default=-1)
    ls.set_defaults(func=cli_ls)

    show = subparsers.add_parser("show", help="show details of an entry")
    show.add_argument("id", help="ID of the entry", type=int)
    show.set_defaults(func=cli_show)

    stats = subparsers.add_parser("stats")
    stats.set_defaults(func=cli_stats)

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
        parsed["segments"] = args.segments
    if hasattr(args, "gpx") and args.gpx:
        gpxpath = Path(args.gpx)
        if not gpxpath.exists():
            print(f"file not found: {args.gpx}")
            sys.exit(1)
        with open(gpxpath) as f:
            parsed["gpx"] = f.read()
    return parsed


@pretty.pretty_errors
def main():
    args = get_args()
    if args.config:
        config = get_config(args.config)
    else:
        config = get_config()
    db_path = get_db_path(config)

    with closing(get_database(config)) as database:
        if not db_path.exists():
            database.migrate()
            print(f"created a new DB at {db_path}")
        else:
            database.migrate()

        args.func(database, args)


if __name__ == "__main__":
    main()
