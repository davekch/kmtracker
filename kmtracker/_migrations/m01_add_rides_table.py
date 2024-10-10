from sqlite3 import Cursor


def run(cursor: Cursor):
    cursor.execute(f"""
        CREATE TABLE rides (
            id INTEGER PRIMARY KEY,
            distance_km REAL NOT NULL,
            timestamp TEXT NOT NULL,
            duration TEXT,
            comment TEXT,
            segments INTEGER DEFAULT 1 CHECK(segments > 0)
        )
    """)

