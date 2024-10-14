A very simple CLI tool to track distance and duration of rides.

## installation
```bash
pip install git+https://github.com/davekch/kmtracker.git
```

## usage

Enter a ride:
```
$ kmtracker add 17 --duration 0:53 --comment "to the lake"   
Success!✨ Added a new ride:
┏━━━━┳━━━━━━━━━━━━┳━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━┳━━━━━━━━━━┳━━━━━┓
┃ ID ┃ Date       ┃ Distance (km) ┃ Duration (hh:mm:ss) ┃ Comment     ┃ Segments ┃ GPX ┃
┡━━━━╇━━━━━━━━━━━━╇━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━╇━━━━━━━━━━╇━━━━━┩
│ 5  │ 2024-10-11 │ 17.0          │ 00:53:00            │ to the lake │ 1        │  -  │
└────┴────────────┴───────────────┴─────────────────────┴─────────────┴──────────┴─────┘
```

Change entries:
```
$ kmtracker add 12                                        
Success!✨ Added a new ride:
┏━━━━┳━━━━━━━━━━━━┳━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━┳━━━━━━━━━━┳━━━━━┓
┃ ID ┃ Date       ┃ Distance (km) ┃ Duration (hh:mm:ss) ┃ Comment ┃ Segments ┃ GPX ┃
┡━━━━╇━━━━━━━━━━━━╇━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━╇━━━━━━━━━━╇━━━━━┩
│ 6  │ 2024-10-11 │ 12.0          │                     │         │ 1        │  -  │
└────┴────────────┴───────────────┴─────────────────────┴─────────┴──────────┴─────┘
$ kmtracker amend --duration 0:24
Changed the latest entry:
┏━━━━┳━━━━━━━━━━━━┳━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━┳━━━━━━━━━━┳━━━━━┓
┃ ID ┃ Date       ┃ Distance (km) ┃ Duration (hh:mm:ss) ┃ Comment ┃ Segments ┃ GPX ┃
┡━━━━╇━━━━━━━━━━━━╇━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━╇━━━━━━━━━━╇━━━━━┩
│ 6  │ 2024-10-11 │ 12.0          │ 00:24:00            │         │ 1        │  -  │
└────┴────────────┴───────────────┴─────────────────────┴─────────┴──────────┴─────┘
```

list entries:
```
$ kmtracker ls                   
┏━━━━┳━━━━━━━━━━━━┳━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━┳━━━━━┓
┃ ID ┃ Date       ┃ Distance (km) ┃ Duration (hh:mm:ss) ┃ Comment             ┃ Segments ┃ GPX ┃
┡━━━━╇━━━━━━━━━━━━╇━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━╇━━━━━┩
│ 3  │ 2024-10-09 │ 26.8          │                     │ work there and back │ 2        │  -  │
│ 2  │ 2024-10-10 │ 13.4          │ 00:35:00            │ work                │ 1        │  -  │
│ 1  │ 2024-10-11 │ 13.4          │ 00:39:00            │ work                │ 1        │  -  │
│ 5  │ 2024-10-11 │ 17.0          │ 00:53:00            │ to the lake         │ 1        │  -  │
│ 6  │ 2024-10-11 │ 12.0          │ 00:24:00            │                     │ 1        │  -  │
└────┴────────────┴───────────────┴─────────────────────┴─────────────────────┴──────────┴─────┘
```

get some stats:
```
$ kmtracker stats
total distance           : 147.6km (7 rides)
longest ride             : 65.0km (on 2024-10-08)
maximum distance on a day: 65.0km (on 2024-10-08)
average speed            : 23.6km/h
fastest ride             : 30.0km/h (on 2024-10-11)
```

you can also add entries by loading a gpx file:
```
$ kmtracker loadgpx mycooltrack.gpx
┏━━━━┳━━━━━━━━━━━━┳━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━┳━━━━━━━━━━┳━━━━━┓
┃ ID ┃ Date       ┃ Distance (km) ┃ Duration (hh:mm:ss) ┃ Avg. speed (km/h) ┃ Comment       ┃ Segments ┃ GPX ┃
┡━━━━╇━━━━━━━━━━━━╇━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━╇━━━━━━━━━━╇━━━━━┩
│ 8  │ 2024-10-12 │ 38.5          │ 01:40:56            │ 22.9              │ my cool track │ 1        │ ✅  │
└────┴────────────┴───────────────┴─────────────────────┴───────────────────┴───────────────┴──────────┴─────┘
```

and get detailed information on the ride:

```
$ kmtracker show 8                 
┏━━━━┳━━━━━━━━━━━━┳━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━┳━━━━━━━━━━┳━━━━━┓
┃ ID ┃ Date       ┃ Distance (km) ┃ Duration (hh:mm:ss) ┃ Avg. speed (km/h) ┃ Comment       ┃ Segments ┃ GPX ┃
┡━━━━╇━━━━━━━━━━━━╇━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━╇━━━━━━━━━━╇━━━━━┩
│ 8  │ 2024-10-12 │ 38.5          │ 01:40:56            │ 22.9              │ my cool track │ 1        │ ✅  │
└────┴────────────┴───────────────┴─────────────────────┴───────────────────┴───────────────┴──────────┴─────┘
time in motion         : 01:36:15
time at rest           : 00:04:40
average speed in motion: 24.0 km/h
maximum speed          : 33.1 km/h
uphill                 : 107.0 m
downhill               : 105.0 m
```

for more see `kmtracker --help` or `kmtracker <command> --help`.
