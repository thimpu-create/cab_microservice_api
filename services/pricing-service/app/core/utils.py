"""
Utility functions for pricing calculations.
"""
import math
from datetime import datetime, time
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


def is_peak_hours(
    current_time: datetime,
    start_time_str: str,
    end_time_str: str,
    day_of_week: Optional[int] = None
) -> bool:
    """
    Check if current time falls within peak hours.
    
    Args:
        current_time: Current datetime
        start_time_str: Start time in "HH:MM" format (24-hour)
        end_time_str: End time in "HH:MM" format (24-hour)
        day_of_week: Day of week (0=Monday, 6=Sunday, None=all days)
    
    Returns:
        True if within peak hours
    """
    # Check day of week
    if day_of_week is not None:
        if current_time.weekday() != day_of_week:
            return False
    
    # Parse time strings
    start_hour, start_minute = map(int, start_time_str.split(":"))
    end_hour, end_minute = map(int, end_time_str.split(":"))
    
    start_time = time(start_hour, start_minute)
    end_time = time(end_hour, end_minute)
    current_time_only = current_time.time()
    
    # Handle time ranges that span midnight
    if start_time <= end_time:
        return start_time <= current_time_only <= end_time
    else:
        # Range spans midnight (e.g., 22:00 to 02:00)
        return current_time_only >= start_time or current_time_only <= end_time
