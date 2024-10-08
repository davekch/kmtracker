from configparser import ConfigParser
from pathlib import Path
from datetime import datetime, timedelta

from kmtracker.db import get_db_connection
from kmtracker import db


CONFIG_PATH = Path("~/.config/kmtracker.cfg").expanduser()
DEFAULT_DB_PATH = "~/.kmtracker.sqlite3"


def get_config() -> ConfigParser:
    config = ConfigParser()
    if not CONFIG_PATH.exists():
        print("✨Welcome to kmtracker!✨\n")
        config["db"] = {
            "path": input(f"database file [{DEFAULT_DB_PATH}]: ") or DEFAULT_DB_PATH
        }
        with open(CONFIG_PATH, "w") as f:
            config.write(f)
            print(f"saved config to {CONFIG_PATH}")
    else:
        config.read([CONFIG_PATH])
    return config


def get_db_path(config: ConfigParser) -> Path:
    return Path(config["db"]["path"]).expanduser().resolve()


def add(
    config: ConfigParser,
    distance: float,
    timestamp: datetime,
    duration: timedelta = None,
    comment: str = None,
    segments: int = 1,
):
    with get_db_connection(get_db_path(config)) as connection:
        db.add_entry(connection, distance, timestamp, duration, comment, segments)