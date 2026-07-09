import math
import csv
from decimal import Decimal
from pathlib import Path
from typing import Any

import requests
from geopy.geocoders import Nominatim
from django.conf import settings

from .models import FuelStation


DATASET_PATH = Path(settings.BASE_DIR) / 'fuel-prices-for-be-assessment.csv'
LOCATION_COORDINATES = {
    'new york, ny': (40.7128, -74.0060),
    'new york': (40.7128, -74.0060),
    'los angeles, ca': (34.0522, -118.2437),
    'los angeles': (34.0522, -118.2437),
    'chicago, il': (41.8781, -87.6298),
    'chicago': (41.8781, -87.6298),
    'houston, tx': (29.7604, -95.3698),
    'houston': (29.7604, -95.3698),
    'phoenix, az': (33.4484, -112.0740),
    'phoenix': (33.4484, -112.0740),
    'san antonio, tx': (29.4241, -98.4936),
    'san diego, ca': (32.7157, -117.1611),
    'san jose, ca': (37.3382, -121.8863),
    'dallas, tx': (32.7767, -96.7970),
    'austin, tx': (30.2672, -97.7431),
    'jacksonville, fl': (30.3322, -81.6557),
    'fort worth, tx': (32.7555, -97.3308),
    'columbus, oh': (39.9612, -82.9988),
    'charlotte, nc': (35.2271, -80.8431),
    'san francisco, ca': (37.7749, -122.4194),
    'indianapolis, in': (39.7684, -86.1581),
    'seattle, wa': (47.6062, -122.3321),
    'denver, co': (39.7392, -104.9903),
    'washington, dc': (38.9072, -77.0369),
    'washington': (38.9072, -77.0369),
    'boston, ma': (42.3601, -71.0589),
    'boston': (42.3601, -71.0589),
    'nashville, tn': (36.1627, -86.7816),
    'memphis, tn': (35.1495, -90.0490),
    'atlanta, ga': (33.7490, -84.3880),
    'miami, fl': (25.7617, -80.1918),
    'detroit, mi': (42.3314, -83.0458),
    'portland, or': (45.5152, -122.6784),
    'philadelphia, pa': (39.9526, -75.1652),
    'oklahoma city, ok': (35.4676, -97.5164),
    'albuquerque, nm': (35.1107, -106.6100),
    'las vegas, nv': (36.1699, -115.1398),
    'kansas city, mo': (39.0997, -94.5786),
    'minneapolis, mn': (44.9778, -93.2650),
    'tulsa, ok': (36.1540, -95.9928),
    'arlington, tx': (32.7357, -97.1081),
    'wichita, ks': (37.6872, -97.3301),
    'baltimore, md': (39.2904, -76.6122),
}

STATE_COORDINATES = {
    'AL': (32.8067, -86.7911),
    'AZ': (34.0489, -111.0937),
    'AR': (34.7998, -92.1990),
    'CA': (36.7783, -119.4179),
    'CO': (39.5501, -105.7821),
    'CT': (41.6032, -73.0877),
    'DE': (39.0099, -75.5277),
    'FL': (27.9944, -81.7603),
    'GA': (32.1656, -82.9001),
    'IA': (41.8780, -93.0977),
    'ID': (44.0682, -114.7420),
    'IL': (39.7817, -89.6501),
    'IN': (39.7684, -86.1581),
    'KS': (38.9717, -95.2353),
    'KY': (37.8393, -84.2700),
    'LA': (30.9843, -91.9623),
    'MA': (42.4072, -71.3824),
    'MD': (39.0458, -76.6413),
    'ME': (45.2538, -69.4455),
    'MI': (44.3148, -85.6024),
    'MN': (46.7296, -94.6859),
    'MO': (38.6270, -90.1994),
    'MS': (32.3547, -89.3985),
    'MT': (46.8797, -110.3626),
    'NC': (35.7596, -79.0193),
    'ND': (47.5515, -101.0020),
    'NE': (41.4925, -99.9018),
    'NH': (43.1939, -71.5724),
    'NJ': (40.0583, -74.4057),
    'NM': (34.5199, -105.8701),
    'NV': (38.8026, -116.4194),
    'NY': (42.9538, -75.5268),
    'OH': (40.4173, -82.9071),
    'OK': (35.4676, -97.5164),
    'OR': (43.8041, -120.5542),
    'PA': (41.2033, -77.1945),
    'RI': (41.5801, -71.4774),
    'SC': (33.8361, -81.1637),
    'SD': (43.9695, -99.9018),
    'TN': (35.5175, -86.5804),
    'TX': (31.9686, -99.9018),
    'UT': (39.32098, -111.0937),
    'VA': (37.4316, -78.6569),
    'VT': (44.5588, -72.5778),
    'WA': (47.7511, -120.7401),
    'WI': (44.5000, -89.5000),
    'WV': (38.5976, -80.4549),
    'WY': (43.07597, -107.2903),
}


class RoutePlanningError(Exception):
    pass


def haversine_miles(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    radius = 3958.7613
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    a = (
        math.sin(delta_phi / 2) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2
    )
    return radius * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def geocode_location(location: str | dict[str, Any] | tuple[float, float]) -> dict[str, float]:
    if isinstance(location, dict):
        if 'lat' in location and 'lon' in location:
            return {'lat': float(location['lat']), 'lon': float(location['lon'])}
        raise RoutePlanningError('Location dictionary must include lat/lon keys.')

    if isinstance(location, (tuple, list)) and len(location) == 2:
        return {'lat': float(location[0]), 'lon': float(location[1])}

    if not isinstance(location, str) or not location.strip():
        raise RoutePlanningError('A non-empty start or finish location is required.')

    normalized = location.strip().lower()
    if normalized in LOCATION_COORDINATES:
        lat, lon = LOCATION_COORDINATES[normalized]
        return {'lat': lat, 'lon': lon}

    geolocator = Nominatim(user_agent='fuel-route-api')
    result = geolocator.geocode(f'{location}, USA', exactly_one=True, timeout=10)
    if result is None:
        raise RoutePlanningError(f'Unable to geocode location: {location}')
    return {'lat': result.latitude, 'lon': result.longitude}


def get_route_geometry(start: dict[str, float], finish: dict[str, float]) -> dict[str, Any]:
    start_lon = start['lon']
    start_lat = start['lat']
    finish_lon = finish['lon']
    finish_lat = finish['lat']
    url = (
        'https://router.project-osrm.org/route/v1/driving/'
        f'{start_lon},{start_lat};{finish_lon},{finish_lat}'
        '?overview=full&geometries=geojson&steps=false&alternatives=false'
    )
    response = requests.get(url, timeout=20)
    response.raise_for_status()
    payload = response.json()
    if not payload.get('routes'):
        raise RoutePlanningError('Routing service returned no route.')
    route = payload['routes'][0]
    return {
        'distance_meters': route['distance'],
        'duration_seconds': route['duration'],
        'geometry': route['geometry']['coordinates'],
    }


def build_route_points(route_geometry: list[list[float]]) -> list[dict[str, float]]:
    if len(route_geometry) > 250:
        stride = max(1, len(route_geometry) // 250)
        sampled_geometry = route_geometry[::stride]
        if sampled_geometry[-1] != route_geometry[-1]:
            sampled_geometry.append(route_geometry[-1])
    else:
        sampled_geometry = route_geometry

    points: list[dict[str, float]] = []
    total = 0.0
    previous: tuple[float, float] | None = None
    for lon, lat in sampled_geometry:
        if previous is None:
            points.append({'lat': lat, 'lon': lon, 'distance_from_start_miles': 0.0})
        else:
            segment = haversine_miles(previous[0], previous[1], lat, lon)
            total += segment
            points.append({'lat': lat, 'lon': lon, 'distance_from_start_miles': total})
        previous = (lat, lon)
    return points


def project_point_to_route(route_points: list[dict[str, float]], lat: float, lon: float) -> tuple[float, float]:
    best_distance = float('inf')
    best_distance_along_route = 0.0
    for index in range(len(route_points) - 1):
        start = route_points[index]
        end = route_points[index + 1]
        start_lat = start['lat']
        start_lon = start['lon']
        end_lat = end['lat']
        end_lon = end['lon']
        start_miles = start['distance_from_start_miles']
        end_miles = end['distance_from_start_miles']
        segment_length = end_miles - start_miles

        if segment_length <= 0:
            continue

        dx = end_lon - start_lon
        dy = end_lat - start_lat
        if dx == 0 and dy == 0:
            candidate_distance = haversine_miles(start_lat, start_lon, lat, lon)
            candidate_along_route = start_miles
        else:
            approach = ((lat - start_lat) * dx + (lon - start_lon) * dy) / (dx * dx + dy * dy)
            approach = max(0.0, min(1.0, approach))
            projected_lat = start_lat + approach * dy
            projected_lon = start_lon + approach * dx
            candidate_distance = haversine_miles(projected_lat, projected_lon, lat, lon)
            candidate_along_route = start_miles + approach * segment_length

        if candidate_distance < best_distance:
            best_distance = candidate_distance
            best_distance_along_route = candidate_along_route
    return best_distance_along_route, best_distance


def get_station_coordinates(station: FuelStation) -> tuple[float, float]:
    if station.latitude is not None and station.longitude is not None:
        return float(station.latitude), float(station.longitude)
    state_key = station.state.upper().strip()
    if state_key in STATE_COORDINATES:
        return STATE_COORDINATES[state_key]
    return (39.5, -98.35)


def plan_fuel_stops(start: str | dict[str, Any] | tuple[float, float], finish: str | dict[str, Any] | tuple[float, float], max_range_miles: float = 500.0, fuel_efficiency_mpg: float = 10.0, max_route_deviation_miles: float = 70.0) -> dict[str, Any]:
    start_coords = geocode_location(start)
    finish_coords = geocode_location(finish)
    route = get_route_geometry(start_coords, finish_coords)
    route_points = build_route_points(route['geometry'])
    route_distance_miles = route['distance_meters'] / 1609.344
    if route_distance_miles <= max_range_miles:
        return {
            'start': start_coords,
            'finish': finish_coords,
            'route': {
                'distance_miles': round(route_distance_miles, 2),
                'duration_minutes': round(route['duration_seconds'] / 60.0, 2),
                'geometry': [
                    {'lat': point['lat'], 'lon': point['lon']} for point in route_points
                ],
            },
            'fuel_strategy': {
                'max_range_miles': max_range_miles,
                'fuel_efficiency_mpg': fuel_efficiency_mpg,
                'stops': [],
                'total_fuel_cost': 0.0,
            },
        }

    stations = list(FuelStation.objects.all().order_by('price')[:120])
    stops: list[dict[str, Any]] = []
    current_miles = 0.0
    total_cost = 0.0
    remaining = route_distance_miles

    while current_miles < route_distance_miles - 1.0 and remaining > max_range_miles + 1.0:
        candidates: list[tuple[Decimal, dict[str, Any]]] = []
        for station in stations:
            station_lat, station_lon = get_station_coordinates(station)
            station_miles, deviation = project_point_to_route(
                route_points,
                station_lat,
                station_lon,
            )
            if station_miles <= current_miles + 0.5:
                continue
            if station_miles > current_miles + max_range_miles + 5.0:
                continue
            if deviation > max_route_deviation_miles:
                continue
            distance_to_stop = station_miles - current_miles
            gallons_needed = distance_to_stop / fuel_efficiency_mpg
            cost = float(station.price) * gallons_needed
            candidates.append((station.price, {
                'station': station,
                'distance_to_stop_miles': distance_to_stop,
                'gallons_needed': round(gallons_needed, 3),
                'estimated_cost': round(cost, 2),
                'projected_route_miles': station_miles,
                'deviation_miles': round(deviation, 2),
            }))

        if not candidates:
            raise RoutePlanningError('Unable to find a suitable fuel stop along the route.')

        candidates.sort(key=lambda item: (item[0], item[1]['projected_route_miles']))
        selected_price, selection = candidates[0]
        stop = selection['station']
        current_miles = selection['projected_route_miles']
        total_cost += selection['estimated_cost']
        remaining = route_distance_miles - current_miles
        station_lat, station_lon = get_station_coordinates(stop)
        stops.append({
            'station_name': stop.name,
            'city': stop.city,
            'state': stop.state,
            'address': stop.address,
            'lat': float(station_lat),
            'lon': float(station_lon),
            'price_per_gallon': float(stop.price),
            'distance_from_previous_miles': round(selection['distance_to_stop_miles'], 2),
            'distance_from_start_miles': round(current_miles, 2),
            'gallons_needed': selection['gallons_needed'],
            'estimated_cost': selection['estimated_cost'],
            'route_deviation_miles': selection['deviation_miles'],
        })

    return {
        'start': start_coords,
        'finish': finish_coords,
        'route': {
            'distance_miles': round(route_distance_miles, 2),
            'duration_minutes': round(route['duration_seconds'] / 60.0, 2),
            'geometry': [
                {'lat': point['lat'], 'lon': point['lon']} for point in route_points
            ],
        },
        'fuel_strategy': {
            'max_range_miles': max_range_miles,
            'fuel_efficiency_mpg': fuel_efficiency_mpg,
            'stops': stops,
            'total_fuel_cost': round(total_cost, 2),
        },
    }


def import_station_prices() -> int:
    if FuelStation.objects.exists():
        return FuelStation.objects.count()

    with DATASET_PATH.open(newline='', encoding='utf-8-sig') as handle:
        reader = csv.DictReader(handle)
        for row_number, row in enumerate(reader, start=2):
            if not row.get('City') or not row.get('State'):
                continue
            price = Decimal(row['Retail Price'].strip())
            FuelStation.objects.create(
                name=row['Truckstop Name'].strip(),
                address=row['Address'].strip(),
                city=row['City'].strip(),
                state=row['State'].strip(),
                price=price,
                source_row=row_number,
            )
    return FuelStation.objects.count()
