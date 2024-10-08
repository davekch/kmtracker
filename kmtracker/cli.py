import argparse
import dateutil
import sys
from datetime import datetime, timedelta
import dateutil.parser
from pathlib import Path

from kmtracker import db
from kmtracker import get_config


def get_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command")

    add = subparsers.add_parser("add", help="add a new ride")
    add.add_argument("distance", help="distance in km")
    add.add_argument("-t", "--timestamp", help="datetime of the ride")
    add.add_argument("-d", "--duration", help="duration of the ride")
    add.add_argument("-c", "--comment")
    add.add_argument("-s", "--segments", help="split this ride into n segments")

    args = parser.parse_args()
    return args


def parse_add_args(args: argparse.Namespace) -> dict:
    parsed = {}
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
            hours, minutes = args.duration.split(":")
            parsed["duration"] = timedelta(hours=int(hours), minutes=int(minutes))
        except ValueError:
            print(f"invalid duration (must be hh:mm): {args.duration!r}")
            sys.exit(1)
    if args.comment:
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
    db_path = Path(config["db"]["path"]).expanduser().resolve()

    if not db_path.exists():
        db.create_db(db_path)
        print(f"created a new DB at {db_path}")

    if args.command == "add":
        parsed_args = parse_add_args(args)
        with db.get_db_connection(db_path) as connection:
            db.add_entry(connection, **parsed_args)
            print("saved new entry!")


if __name__ == "__main__":
    main()
