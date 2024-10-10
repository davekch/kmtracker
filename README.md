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
┏━━━━┳━━━━━━━━━━━━┳━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━┳━━━━━━━━━━┓
┃ ID ┃ Date       ┃ Distance (km) ┃ Duration (hh:mm:ss) ┃ Comment     ┃ Segments ┃
┡━━━━╇━━━━━━━━━━━━╇━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━╇━━━━━━━━━━┩
│ 5  │ 2024-10-11 │ 17.0          │ 00:53:00            │ to the lake │ 1        │
└────┴────────────┴───────────────┴─────────────────────┴─────────────┴──────────┘
```

Change entries:
```
$ kmtracker add 12                                        
Success!✨ Added a new ride:
┏━━━━┳━━━━━━━━━━━━┳━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━┳━━━━━━━━━━┓
┃ ID ┃ Date       ┃ Distance (km) ┃ Duration (hh:mm:ss) ┃ Comment ┃ Segments ┃
┡━━━━╇━━━━━━━━━━━━╇━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━╇━━━━━━━━━━┩
│ 6  │ 2024-10-11 │ 12.0          │                     │         │ 1        │
└────┴────────────┴───────────────┴─────────────────────┴─────────┴──────────┘
$ kmtracker amend --duration 0:24
Changed the latest entry:
┏━━━━┳━━━━━━━━━━━━┳━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━┳━━━━━━━━━━┓
┃ ID ┃ Date       ┃ Distance (km) ┃ Duration (hh:mm:ss) ┃ Comment ┃ Segments ┃
┡━━━━╇━━━━━━━━━━━━╇━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━╇━━━━━━━━━━┩
│ 6  │ 2024-10-11 │ 12.0          │ 00:24:00            │         │ 1        │
└────┴────────────┴───────────────┴─────────────────────┴─────────┴──────────┘
```

list entries:
```
$ kmtracker ls                   
┏━━━━┳━━━━━━━━━━━━┳━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━┓
┃ ID ┃ Date       ┃ Distance (km) ┃ Duration (hh:mm:ss) ┃ Comment             ┃ Segments ┃
┡━━━━╇━━━━━━━━━━━━╇━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━┩
│ 3  │ 2024-10-09 │ 26.8          │                     │ work there and back │ 2        │
│ 2  │ 2024-10-10 │ 13.4          │ 00:35:00            │ work                │ 1        │
│ 1  │ 2024-10-11 │ 13.4          │ 00:39:00            │ work                │ 1        │
│ 5  │ 2024-10-11 │ 17.0          │ 00:53:00            │ to the lake         │ 1        │
│ 6  │ 2024-10-11 │ 12.0          │ 00:24:00            │                     │ 1        │
└────┴────────────┴───────────────┴─────────────────────┴─────────────────────┴──────────┘
```

get some stats:
```
$ kmtracker stats
total distance           : 147.6km (7 rides)
longest ride             : 65.0km (on 2024-10-08)
maximum distance on a day: 65.0km (on 2024-10-08)
average velocity         : 23.6km/h
fastest ride             : 30.0km/h (on 2024-10-11)
```

for more see `kmtracker --help` or `kmtracker <command> --help`.
