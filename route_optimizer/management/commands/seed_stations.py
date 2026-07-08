import csv
import time
from decimal import Decimal

from django.core.management.base import BaseCommand
from geopy.geocoders import Nominatim

from route_optimizer.models import FuelStation
from route_optimizer.services import DATASET_PATH


class Command(BaseCommand):
    help = 'Load fuel price stations from the provided CSV dataset.'

    def handle(self, *args, **options):
        geolocator = Nominatim(user_agent='fuel-route-api')
        if not FuelStation.objects.exists():
            with DATASET_PATH.open(newline='', encoding='utf-8-sig') as handle:
                reader = csv.DictReader(handle)
                for row_number, row in enumerate(reader, start=2):
                    if not row.get('City') or not row.get('State'):
                        continue
                    FuelStation.objects.create(
                        name=row['Truckstop Name'].strip(),
                        address=row['Address'].strip(),
                        city=row['City'].strip(),
                        state=row['State'].strip(),
                        price=Decimal(row['Retail Price'].strip()),
                        source_row=row_number,
                    )

        stations_to_geocode = FuelStation.objects.filter(latitude__isnull=True, longitude__isnull=True)
        for station in stations_to_geocode:
            query = f"{station.address}, {station.city}, {station.state}, USA"
            try:
                result = geolocator.geocode(query, exactly_one=True, timeout=10)
                if result is not None:
                    station.latitude = result.latitude
                    station.longitude = result.longitude
                    station.geocoded = True
                    station.save(update_fields=['latitude', 'longitude', 'geocoded'])
                    else:
                        station.latitude = None
                        station.longitude = None
                        station.geocoded = False
                        station.save(update_fields=['latitude', 'longitude', 'geocoded'])
                    time.sleep(0.9)
                except Exception as exc:  # pragma: no cover - network failure guard
                    station.latitude = None
                    station.longitude = None
                    station.geocoded = False
                    station.save(update_fields=['latitude', 'longitude', 'geocoded'])
