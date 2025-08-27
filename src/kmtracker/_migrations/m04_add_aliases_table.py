from sqlite3 import Cursor


def run(cursor: Cursor):
    cursor.execute(f"""
        CREATE TABLE aliases (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            distance_km REAL,
            duration_s INTEGER CHECK(duration_s > 0),
            comment TEXT,
            segments INTEGER DEFAULT 1 CHECK(segments > 0)
        )
    """)
