import configparser
from pathlib import Path


CONFIG_PATH = Path("~/.config/kmtracker.cfg").expanduser()
DEFAULT_DB_PATH = "~/.kmtracker.sqlite3"


def get_config() -> configparser.ConfigParser:
    config = configparser.ConfigParser()
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
