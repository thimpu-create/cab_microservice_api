"""
Utility functions for ride management.
"""
import math
from typing import Tuple, Optional


def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate the great circle distance between two points on Earth (in kilometers).
    Uses the Haversine formula.
    """
    # Radius of Earth in kilometers
    R = 6371.0
    
    # Convert latitude and longitude from degrees to radians
    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)
    
    # Difference in coordinates
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad
    
    # Haversine formula
    a = math.sin(dlat / 2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    
    distance = R * c
    return distance


def calculate_eta(distance_km: float, average_speed_kmh: float = 30.0) -> int:
    """
    Calculate estimated time of arrival in minutes.
    
    Args:
        distance_km: Distance in kilometers
        average_speed_kmh: Average speed in km/h (default 30 km/h for city traffic)
    
    Returns:
        ETA in minutes (rounded)
    """
    if distance_km <= 0:
        return 0
    
    time_hours = distance_km / average_speed_kmh
    time_minutes = time_hours * 60
    
    return max(1, int(round(time_minutes)))


def calculate_eta_to_pickup(
    driver_lat: float,
    driver_lon: float,
    pickup_lat: float,
    pickup_lon: float,
    average_speed_kmh: float = 30.0
) -> Tuple[float, int]:
    """
    Calculate distance and ETA from driver to pickup location.
    
    Returns:
        (distance_km, eta_minutes)
    """
    distance = calculate_distance(driver_lat, driver_lon, pickup_lat, pickup_lon)
    eta = calculate_eta(distance, average_speed_kmh)
    
    return distance, eta


def calculate_eta_to_dropoff(
    current_lat: float,
    current_lon: float,
    dropoff_lat: float,
    dropoff_lon: float,
    average_speed_kmh: float = 30.0
) -> Tuple[float, int]:
    """
    Calculate distance and ETA from current location to dropoff.
    
    Returns:
        (distance_km, eta_minutes)
    """
    distance = calculate_distance(current_lat, current_lon, dropoff_lat, dropoff_lon)
    eta = calculate_eta(distance, average_speed_kmh)
    
    return distance, eta
