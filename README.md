# Fuel-route Django API

This project implements a Django API that accepts a start and finish location in the USA, requests a driving route from the OpenStreetMap Routing API, and selects fuel stops along the route based on the cheapest available fuel prices from the provided CSV dataset.

## Run locally

```bash
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_stations
python manage.py runserver
```

## Example request

```bash
curl "http://127.0.0.1:8000/api/route/?start=New%20York,%20NY&finish=Los%20Angeles,%20CA"
```

The response includes:
- the route geometry
- the total route distance and duration
- the fuel-stop plan with estimated cost per leg
- the total fuel cost assuming 10 miles per gallon
