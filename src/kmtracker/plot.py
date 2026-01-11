from collections import Counter
import dayplot
import matplotlib.pyplot as plt

from kmtracker.db import Database, Ride


def prepare_data(db: Database) -> Counter:
    rides = Ride.get_latest_entries(db, -1)
    kms = Counter()
    for ride in rides:
        kms[ride.timestamp.date().isoformat()] += ride.distance
    return kms


def create_plot(rides: Counter):
    mindate = min(rides.keys())
    maxdate = max(rides.keys())
    # years = list(range(mindate.year, maxdate.year+1))
    years = list(range(int(mindate[:4]), int(maxdate[:4])+1))
    nyears = len(years)

    fig, axs = plt.subplots(nrows=nyears, figsize=(15, nyears*3))
    if nyears == 1:
        axs = [axs]

    for i, year in enumerate(years):
        start = f"{year}-01-01"
        # start = start if start > mindate else mindate
        end = f"{year}-12-31"
        # end = end if end < maxdate else maxdate
        dayplot.calendar(
            dates=rides.keys(),
            values=rides.values(),
            start_date=start,
            end_date=end,
            week_starts_on="Monday",
            ax=axs[i],
        )
        axs[i].text(s=str(year), x=-4, y=3.5, size=30, rotation=90, color="#aaa", va="center")


    fig.tight_layout()
    return fig


def show_plot(db: Database):
    create_plot(prepare_data(db))
    plt.show()
