from fastapi import FastAPI, Request, Depends
from fastapi.templating import Jinja2Templates
from pathlib import Path
import os

from kmtracker import get_config, get_database
from kmtracker.db import Database, Ride, FloatField


CONFIG_PATH = Path(os.environ.get("KMTRACKER_CONFIG_PATH")).resolve()
config = get_config(CONFIG_PATH)
templates = Jinja2Templates(Path(__file__).parent / "templates")
app = FastAPI()


def db_connection():
    db = get_database(config)
    try:
        yield db
    finally:
        db.close()


@app.get("/")
def index(request: Request):
    return templates.TemplateResponse(request=request, name="index.html")


@app.get("/rides")
def rides(request: Request, db: Database=Depends(db_connection)):
    rides_objs = Ride.get_latest_entries(db, -1)
    rides = []
    for ride in rides_objs:
        data = ride.serialize_pretty()
        data["speed"] = FloatField.serialize_pretty(ride.speed)
        data["gpx"] = "✅" if ride.gpx else "-"
        rides.append(data)
    return templates.TemplateResponse(
        request=request,
        name="components/_table.html",
        context={
            "columns": [
                Ride.columns.pk.field.display_name,
                Ride.columns.timestamp.field.display_name,
                Ride.columns.distance.field.display_name,
                Ride.columns.duration.field.display_name,
                "Avg. speed (km/h)",
                Ride.columns.comment.field.display_name,
                Ride.columns.segments.field.display_name,
                Ride.columns.gpx.field.display_name,
            ],
            "keys": [
                Ride.columns.pk.name,
                Ride.columns.timestamp.name,
                Ride.columns.distance.name,
                Ride.columns.duration.name,
                "speed",
                Ride.columns.comment.name,
                Ride.columns.segments.name,
                "gpx",
            ],
            "rows": rides,
        }
    )
