#!/usr/bin/python

import json
import os

import requests

CLIENT_ID = 55545
CLIENT_SECRET = os.environ['STRAVA_CLIENT_SECRET']
AUTHORIZE_URL = f'http://www.strava.com/oauth/authorize?client_id={CLIENT_ID}&response_type=code&redirect_uri=http://localhost/exchange_token&approval_prompt=force&scope=read,activity:read'
TOKEN_URL = 'https://www.strava.com/oauth/token'

if __name__ == '__main__':
    print('Visit:', AUTHORIZE_URL)
    code = input('Copy the code:')

    token_fields = {
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
        'code': code.strip(),
        'grant_type': 'authorization_code'
    }
    response = requests.post(TOKEN_URL, data=token_fields)
    response.raise_for_status()
    token_data = response.json()
    print('refresh_token:', token_data['refresh_token'])
    print('access_token:', token_data['access_token'])
    with open('strava_token.json', 'w') as f:
        json.dump(token_data, f)
