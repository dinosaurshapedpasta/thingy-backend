"""
Maps Service Module

Handles distance/time calculations using OpenRouteService API.
https://openrouteservice.org/dev/#/api-docs
"""

import os
import httpx
from typing import List, Tuple, Optional

# Configuration - set these via environment variables
ORS_API_KEY = os.getenv("ORS_API_KEY", "")
ORS_BASE_URL = os.getenv("ORS_BASE_URL", "https://api.openrouteservice.org")


async def calculate_distance_matrix(
    origins: List[Tuple[float, float]],
    destinations: List[Tuple[float, float]]
) -> List[List[float]]:
    """
    Calculate travel time matrix from origins to destinations using OpenRouteService.
    
    Args:
        origins: List of (latitude, longitude) tuples
        destinations: List of (latitude, longitude) tuples
    
    Returns:
        Matrix of travel times in minutes [origins x destinations]
    """
    if not ORS_API_KEY:
        raise ValueError("ORS_API_KEY environment variable not set")
    
    # ORS expects coordinates as [longitude, latitude] (GeoJSON format)
    all_locations = []
    for lat, lng in origins:
        all_locations.append([lng, lat])
    for lat, lng in destinations:
        all_locations.append([lng, lat])
    
    # Build source and destination indices
    num_origins = len(origins)
    sources = list(range(num_origins))
    destinations_indices = list(range(num_origins, len(all_locations)))
    
    url = f"{ORS_BASE_URL}/v2/matrix/driving-car"
    headers = {
        "Authorization": f"Bearer {ORS_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "locations": all_locations,
        "sources": sources,
        "destinations": destinations_indices,
        "metrics": ["duration"],  # We want travel time
        "units": "m"
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=payload, headers=headers)
        
        if response.status_code != 200:
            raise Exception(f"OpenRouteService API error: {response.status_code} - {response.text}")
        
        data = response.json()
    
    # Extract durations (in seconds) and convert to minutes
    durations = data.get("durations", [])
    matrix = []
    for row in durations:
        row_times = [d / 60.0 if d is not None else float('inf') for d in row]
        matrix.append(row_times)
    
    return matrix


async def calculate_route(
    origin: Tuple[float, float],
    destination: Tuple[float, float],
    waypoints: Optional[List[Tuple[float, float]]] = None
) -> dict:
    """
    Calculate a route with optional waypoints using OpenRouteService.
    
    Args:
        origin: (latitude, longitude) tuple
        destination: (latitude, longitude) tuple
        waypoints: Optional list of (latitude, longitude) tuples
    
    Returns:
        {
            "distance": float (km),
            "duration": float (minutes),
            "geometry": str (encoded polyline)
        }
    """
    if not ORS_API_KEY:
        raise ValueError("ORS_API_KEY environment variable not set")
    
    # Build coordinates list [lng, lat] format
    coords = [[origin[1], origin[0]]]
    if waypoints:
        for wp in waypoints:
            coords.append([wp[1], wp[0]])
    coords.append([destination[1], destination[0]])
    
    url = f"{ORS_BASE_URL}/v2/directions/driving-car"
    headers = {
        "Authorization": f"Bearer {ORS_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "coordinates": coords,
        "instructions": False,
        "geometry": True
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=payload, headers=headers)
        
        if response.status_code != 200:
            raise Exception(f"OpenRouteService API error: {response.status_code} - {response.text}")
        
        data = response.json()
    
    # Extract route summary
    routes = data.get("routes", [])
    if not routes:
        return {"distance": 0, "duration": 0, "geometry": ""}
    
    route = routes[0]
    summary = route.get("summary", {})
    
    return {
        "distance": summary.get("distance", 0) / 1000.0,  # meters to km
        "duration": summary.get("duration", 0) / 60.0,    # seconds to minutes
        "geometry": route.get("geometry", "")
    }


async def geocode(address: str) -> Optional[Tuple[float, float]]:
    """
    Convert an address to coordinates using OpenRouteService Geocoding.
    
    Args:
        address: Address string to geocode
    
    Returns:
        (latitude, longitude) tuple or None if not found
    """
    if not ORS_API_KEY:
        raise ValueError("ORS_API_KEY environment variable not set")
    
    url = f"{ORS_BASE_URL}/geocode/search"
    headers = {
        "Authorization": f"Bearer {ORS_API_KEY}"
    }
    params = {
        "text": address,
        "size": 1
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.get(url, params=params, headers=headers)
        
        if response.status_code != 200:
            return None
        
        data = response.json()
    
    features = data.get("features", [])
    if not features:
        return None
    
    coords = features[0].get("geometry", {}).get("coordinates", [])
    if len(coords) >= 2:
        # ORS returns [lng, lat], we return (lat, lng)
        return (coords[1], coords[0])
    
    return None


async def reverse_geocode(lat: float, lng: float) -> Optional[str]:
    """
    Convert coordinates to an address using OpenRouteService.
    
    Args:
        lat: Latitude
        lng: Longitude
    
    Returns:
        Address string or None if not found
    """
    if not ORS_API_KEY:
        raise ValueError("ORS_API_KEY environment variable not set")
    
    url = f"{ORS_BASE_URL}/geocode/reverse"
    headers = {
        "Authorization": f"Bearer {ORS_API_KEY}"
    }
    params = {
        "point.lon": lng,
        "point.lat": lat,
        "size": 1
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.get(url, params=params, headers=headers)
        
        if response.status_code != 200:
            return None
        
        data = response.json()
    
    features = data.get("features", [])
    if not features:
        return None
    
    return features[0].get("properties", {}).get("label")


def parse_location_string(location: str) -> Optional[Tuple[float, float]]:
    """
    Parse a location string into (latitude, longitude).
    
    Supports formats:
    - "51.4994,-0.1745" (decimal)
    - "51°29'57.0\"N 0°10'39.3\"W" (DMS)
    """
    import re
    
    # Try decimal format first
    decimal_match = re.match(r'^(-?\d+\.?\d*),\s*(-?\d+\.?\d*)$', location)
    if decimal_match:
        return float(decimal_match.group(1)), float(decimal_match.group(2))
    
    # Try DMS format
    dms_pattern = r"(\d+)°(\d+)'([\d.]+)\"([NS])\s+(\d+)°(\d+)'([\d.]+)\"([EW])"
    dms_match = re.match(dms_pattern, location)
    if dms_match:
        lat_d, lat_m, lat_s, lat_dir = dms_match.groups()[:4]
        lng_d, lng_m, lng_s, lng_dir = dms_match.groups()[4:]
        
        lat = float(lat_d) + float(lat_m)/60 + float(lat_s)/3600
        if lat_dir == 'S':
            lat = -lat
        
        lng = float(lng_d) + float(lng_m)/60 + float(lng_s)/3600
        if lng_dir == 'W':
            lng = -lng
        
        return lat, lng
    
    return None
