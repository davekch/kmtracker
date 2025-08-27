from sqlite3 import Cursor
from datetime import timedelta


def run(cursor: Cursor):
    """
    convert the duration column from text to int and call it duration_s
    """
    # get all durations
    durs = cursor.execute("SELECT id, duration FROM rides").fetchall()
    # convert to seconds
    durs_int = []
    for id, dur in durs:
        if not dur:
            durs_int.append({"id": id, "value": None})
        else:
            h, m, s = dur.split(":")
            d = timedelta(hours=int(h), minutes=int(m), seconds=int(s))
            durs_int.append({"id": id, "value": d.days * 60 * 60 * 24 + d.seconds})
    # create new column
    cursor.execute("ALTER TABLE rides ADD COLUMN duration_s INTEGER CHECK(duration_s > 0)")
    # set values
    cursor.executemany("UPDATE rides SET duration_s = :value WHERE id = :id", durs_int)
    # remove old column
    cursor.execute("ALTER TABLE rides DROP duration")
