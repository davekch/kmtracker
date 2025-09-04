from configparser import ConfigParser
from pathlib import Path
import os

from kmtracker import db


DEFAULT_CONFIG_PATH = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")) / "kmtracker.cfg"
DEFAULT_DB_PATH = "~/.kmtracker.sqlite3"


def get_config(path: Path=DEFAULT_CONFIG_PATH) -> ConfigParser:
    config = ConfigParser()
    if not path.exists():
        print("✨Welcome to kmtracker!✨\n")
        config["db"] = {
            "path": input(f"database file [{DEFAULT_DB_PATH}]: ") or DEFAULT_DB_PATH
        }
        with open(path, "w") as f:
            config.write(f)
            print(f"saved config to {path}")
    else:
        config.read(path)
    return config


def get_db_path(config: ConfigParser) -> Path:
    return Path(config["db"]["path"]).expanduser().resolve()


def get_database(config: ConfigParser) -> db.Database:
    return db.Database(get_db_path(config))
