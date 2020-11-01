#!/usr/bin/python

import json
import os
import time

from datetime import datetime, timedelta

import requests

from dateutil.parser import parse as parse_date
from influxdb import InfluxDBClient

CLIENT_ID = int(os.getenv('STRAVA_CLIENT_ID', '55545'))
CLIENT_SECRET = os.environ['STRAVA_CLIENT_SECRET']

INFLUX_HOST = os.getenv('HOST', 'localhost')
INFLUX_PORT = os.getenv('PORT', '8086')
INFLUX_DB = os.getenv('DATABASE', 'strava')

TOKEN_URL = 'https://www.strava.com/oauth/token'
ACTIVITIES_URL = 'https://www.strava.com/api/v3/athlete/activities'

IMPORT_FROM = os.getenv('IMPORT_FROM', '2020-10-01')


class StravaClient():

    s: requests.Session

    def __init__(self):
        self.s = requests.Session()

        token_data = self._read_token()
        self._set_token(token_data['access_token'])

    def refresh_token(self):
        token_fields = {
            'client_id': CLIENT_ID,
            'client_secret': CLIENT_SECRET,
            'refresh_token': self._read_token()['refresh_token'],
            'grant_type': 'refresh_token',
        }
        response = requests.post(TOKEN_URL, data=token_fields)
        response.raise_for_status()
        token_data = response.json()
        self._write_token(token_data)
        self._set_token(token_data['access_token'])

    def list_activities_since(self, start_date: datetime):
        """Return an unordered sequence of activities after the given date."""
        page_number = 1
        while True:
            params = {
                'page': page_number,
                'after': time.mktime(start_date.utctimetuple()),
                'per_page': 100,
            }
            response = self.s.get(ACTIVITIES_URL, params=params)
            if response.status_code == 401:
                self.refresh_token()
                response = self.s.get(ACTIVITIES_URL)
            response.raise_for_status()

            activities = response.json()
            for activity in activities:
                yield activity
            if len(activities) == 0:
                return

            page_number = page_number + 1

    def get_streams(self, activity_id):
        metrics = [
            'time',
            'distance',
            'latlng',
            'velocity_smooth',
            'altitude',
            'heartrate',
            'cadence',
        ]

        url = f'https://www.strava.com/api/v3/activities/{activity_id}/streams'
        stream_params = {
            'resolution': 'high',
            'keys': [','.join(metrics)]
        }
        response = self.s.get(url, params=stream_params)
        if response.status_code == 401:
            self.refresh_token()
            response = self.s.get(url, params=stream_params)
        response.raise_for_status()
        for stream in response.json():
            if stream['type'] == 'latlng':
                yield {
                    'type': 'lat',
                    'data': [data[0] for data in stream['data']]
                }
                yield {
                    'type': 'lng',
                    'data': [data[1] for data in stream['data']]
                }
            else:
                yield stream

    def _set_token(self, access_token):
        self.s.headers['Authorization'] = f"Bearer {access_token}"

    def _read_token(self):
        with open('strava_token.json') as f:
            return json.load(f)

    def _write_token(self, token_data):
        with open('strava_token.json', 'w') as f:
            json.dump(token_data, f)


if __name__ == '__main__':
    strava_client = StravaClient()

    influx_client = InfluxDBClient(host=INFLUX_HOST, port=INFLUX_PORT)
    influx_client.create_database(INFLUX_DB)
    influx_client.switch_database(INFLUX_DB)

    rs = influx_client.query('select last(distance) from activity')
    last_point = parse_date(next(rs.get_points(), {'time': IMPORT_FROM})['time'])

    activities = sorted(strava_client.list_activities_since(last_point), key=lambda a: a['start_date'])
    for activity in activities:
        measurement = 'activity'
        tags = {
            'name': activity['name'],
            'type': activity['type'],
            'start_date': activity['start_date']
        }

        streams = list(strava_client.get_streams(activity['id']))
        time_stream = [stream for stream in streams if stream['type'] == 'time'][0]
        data_streams = [stream for stream in streams if stream['type'] != 'time']

        stream_names = [stream['type'] for stream in data_streams]
        stream_values = [stream['data'] for stream in data_streams]

        start_date = parse_date(activity['start_date'])

        points = []
        for chunk in zip(time_stream['data'], *stream_values):
            ts = start_date + timedelta(seconds=chunk[0])
            fields = {k: v for k, v in zip(stream_names, chunk[1:])}
            points.append({
                'measurement': measurement,
                'tags': tags,
                'time': ts.isoformat(),
                'fields': fields,
            })
        influx_client.write_points(points)
