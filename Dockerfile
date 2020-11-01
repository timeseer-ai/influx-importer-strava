FROM python:3.8

WORKDIR /usr/src/app

COPY requirements.txt .
RUN pip install -r requirements.txt

VOLUME /usr/src/app/strava_token.json

COPY import-strava-data.py .

CMD ["python", "import-strava-data.py"]
