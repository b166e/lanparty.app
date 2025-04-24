from math import radians, sin, cos, sqrt, atan2
from typing import Optional

def calcular_distancia(lat1: Optional[float], lon1: Optional[float], 
                       lat2: Optional[float], lon2: Optional[float]) -> float:
    """
    Calculate the distance between two coordinates using the Haversine formula.
    Returns distance in meters.
    """
    # Return 0 if any coordinate is None
    if None in [lat1, lon1, lat2, lon2]:
        return 0
    
    # Earth radius in meters
    R = 6371000
    
    # Convert latitude and longitude from degrees to radians
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    
    # Haversine formula
    a = sin(dlat/2)**2 + cos(radians(lat1))*cos(radians(lat2))*sin(dlon/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1-a))
    
    # Distance in meters
    return R * c
