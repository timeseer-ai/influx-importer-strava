# influx-importer-strava

`influx-importer-strava` imports Strava activity data of one athlete into InfluxDB.

The schema looks like:

```
> show tag keys
name: activity
tagKey
------
name
start_date
type
> show field keys
name: activity
fieldKey        fieldType
--------        ---------
altitude        float
cadence         integer
distance        float
heartrate       integer
lat             float
lng             float
velocity_smooth float
```

The data looks like (with `lat` and `lng` redacted):

```
> select * from activity order by time desc limit 3;
{
    "results": [
        {
            "series": [
                {
                    "name": "activity",
                    "columns": [
                        "time",
                        "altitude",
                        "cadence",
                        "distance",
                        "heartrate",
                        "lat",
                        "lng",
                        "name",
                        "start_date",
                        "type",
                        "velocity_smooth"
                    ],
                    "values": [
                        [
                            1604923841000000000,
                            29,
                            82,
                            9138,
                            165,
                            0.000000,
                            0.000000,
                            "Sahara",
                            "2020-11-09T11:23:55Z",
                            "Run",
                            3.8
                        ],
                        [
                            1604923840000000000,
                            29,
                            82,
                            9134,
                            165,
                            0.000000,
                            0.000000,
                            "Sahara",
                            "2020-11-09T11:23:55Z",
                            "Run",
                            3.6
                        ],
                        [
                            1604923839000000000,
                            28.8,
                            82,
                            9130,
                            165,
                            0.000000,
                            0.000000,
                            "Sahara",
                            "2020-11-09T11:23:55Z",
                            "Run",
                            3.6
                        ]
                    ]
                }
            ]
        }
    ]
}
```

## Running Locally

First register a [Strava application](https://developers.strava.com/docs/getting-started/#account)

Set the 'Authorization Callback Domain' to `localhost`.

Make the Client ID and Client Secret available in the environment:

```bash
$ export STRAVA_CLIENT_ID=55545
$ export STRAVA_CLIENT_SECRET=<secret>
```

Fetch the initial access token using the `get-token.py` helper:

```bash
$ python -m venv venv
$ source venv/bin/activate
(venv) $ pip install -r requirements.txt
(venv) $ python get-token.py
```

This will request you to log in to Strava.
Copy the `code` url parameter in the redirect to the script when prompted.

The token will be stored in `strava_token.json`.

Correctly set the `HOST`, `PORT` and `DB` environment variables to point to InfluxDB.

```bash
$ export HOST=localhost
$ export POST=8086
$ export DB=strava
```

The importer will create the database if it does not exist.

Set a start date for the import using `IMPORT_FROM`:

```bash
$ export IMPORT_FROM=2020-10-01
```

Then run the script:

```bash
(venv) $ python import-strava-data.py
```

## Testing in Docker

Start InfluxDB using `docker-compose`:

```bash
$ docker-compose up
```

Then build and run the Docker container:

```bash
$ docker build -t influx-importer-strava .
$ docker run --rm -e STRAVA_CLIENT_SECRET -e HOST=172.17.0.1 -v $PWD/strava_token.json:/usr/src/app/strava_token.json:rw influx-importer-strava:latest
```

Set the environment variables described above as needed by the deployment environment.
The `strava_token.json` file needs to be volume mapped `rw` in the container at `/usr/src/app/strava_token.json`.
