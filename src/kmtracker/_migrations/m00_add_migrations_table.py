from sqlite3 import Cursor


def run(cursor: Cursor):
    cursor.execute(f"""
        CREATE TABLE _migrations (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            timestamp TEXT DEFAULT CURRENT_TIMESTAMP NOT NULL
        )
    """)

