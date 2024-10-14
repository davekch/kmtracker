from sqlite3 import Cursor


def run(cursor: Cursor):
    cursor.execute("ALTER TABLE rides ADD COLUMN gpx TEXT")
