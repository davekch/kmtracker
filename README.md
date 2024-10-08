```bash
$ python kmtracker/cli.py --help   
usage: cli.py [-h] {add,amend,ls} ...

positional arguments:
  {add,amend,ls}
    add           add a new ride
    amend         change the latest entry
    ls            show latest ride

options:
  -h, --help      show this help message and exit
```

```bash
$ python kmtracker/cli.py add --help                                                        
usage: cli.py add [-h] [-t TIMESTAMP] [-d DURATION] [-c COMMENT] [-s SEGMENTS] distance

positional arguments:
  distance              distance in km

options:
  -h, --help            show this help message and exit
  -t TIMESTAMP, --timestamp TIMESTAMP
                        datetime of the ride
  -d DURATION, --duration DURATION
                        duration of the ride
  -c COMMENT, --comment COMMENT
  -s SEGMENTS, --segments SEGMENTS
                        split this ride into n segments
```
