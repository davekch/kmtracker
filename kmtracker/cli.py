import argparse
import dateutil
import sys
from datetime import datetime, timedelta
import dateutil.parser
from pathlib import Path

from kmtracker import db
from kmtracker import (
    get_config,
    get_db_path,
    add,
    amend,
    get_latest,
)


def get_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command")

    add = subparsers.add_parser("add", help="add a new ride")
    add.add_argument("distance", help="distance in km")
    add.add_argument("-t", "--timestamp", help="datetime of the ride")
    add.add_argument("-d", "--duration", help="duration of the ride")
    add.add_argument("-c", "--comment")
    add.add_argument("-s", "--segments", help="split this ride into n segments")

    amend = subparsers.add_parser("amend", help="change the latest entry")
    amend.add_argument("-k", "--distance", help="distance in km")
    amend.add_argument("-t", "--timestamp", help="datetime of the ride")
    amend.add_argument("-d", "--duration", help="duration of the ride (hh:mm or hh:mm:ss)")
    amend.add_argument("-c", "--comment")
    amend.add_argument("-s", "--segments", help="split this ride into n segments")

    ls = subparsers.add_parser("ls", help="show latest ride")
    ls.add_argument("-n", help="number of entries to show", type=int, default=1)

    args = parser.parse_args()
    return args


def parse_add_args(args: argparse.Namespace) -> dict:
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
    else:
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
    return parsed


def main():
    args = get_args()
    config = get_config()
    db_path = get_db_path(config)

    if not db_path.exists():
        db.create_db(db_path)
        print(f"created a new DB at {db_path}")

    if args.command == "add":
        parsed_args = parse_add_args(args)
        add(config, **parsed_args)
    elif args.command == "amend":
        parsed_args = parse_add_args(args)
        amend(config, **parsed_args)
    elif args.command == "ls":
        get_latest(config, args.n)


if __name__ == "__main__":
    main()
