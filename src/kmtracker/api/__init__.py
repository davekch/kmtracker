from fastapi import FastAPI, Request, Depends
from fastapi.templating import Jinja2Templates
from pathlib import Path
import os
from datetime import timedelta, datetime
from pydantic import BaseModel, Field
from typing import Optional

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


class RideForm(BaseModel):
    distance: float
    timestamp: datetime = Field(default_factory=datetime.today)
    duration: Optional[timedelta] = None
    comment: Optional[str] = ""
    segments: Optional[int] = 1


async def clean_rideform(request: Request) -> RideForm:
    form = await request.form()                     # async — run on event loop
    # drop empty-string values so Pydantic will apply defaults for missing fields
    cleaned = {k: v for k, v in dict(form).items() if v != ""}
    return RideForm(**cleaned)

@app.get("/")
def index(request: Request):
    return templates.TemplateResponse(request=request, name="index.html")


@app.get("/rides")
def rides(request: Request, db: Database=Depends(db_connection)):
    rides_objs = Ride.get_latest_entries(db, -1)
    rides = [r.serialize_pretty() for r in rides_objs]
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
            "table_id": "rides",
        }
    )


@app.get("/rides/new")
def rides_new_show_form(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="components/_form_ride.html",
        context=RideForm(distance=0).model_dump(mode="json"),
    )


@app.post("/rides/new")
def rides_new_submit_form(
    request: Request,
    form: RideForm=Depends(clean_rideform),
    db: Database=Depends(db_connection),
):
    ride = Ride(db, **form.model_dump())
    ride.save()
    data = ride.serialize_pretty()
    return templates.TemplateResponse(
        request=request,
        name="components/_table_row.html",
        context={
            "row": data,
            "keys": [
                Ride.columns.pk.name,
                Ride.columns.timestamp.name,
                Ride.columns.distance.name,
                Ride.columns.duration.name,
                "speed",
                Ride.columns.comment.name,
                Ride.columns.segments.name,
                "gpx",]
        }
    )



@app.get("/stats")
def stats(request: Request, db: Database=Depends(db_connection)):
    summary = Ride.get_summary(db)
    streaks = Ride.get_streaks(db)
    if (today := datetime.today().date()) in streaks:
        summary["on_streak"] = True
        summary["current_streak"] = streaks[today]
    elif (yesterday := today - timedelta(days=1)) in streaks:
        summary["keep_up"] = True
        summary["current_streak"] = streaks[yesterday]
    return templates.TemplateResponse(
        request=request,
        name="components/_stats.html",
        context=summary,
    )
