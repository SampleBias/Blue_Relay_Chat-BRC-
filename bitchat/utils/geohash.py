"""
Geohash utilities for Blue Relay Chat RPi 4 client.

This module provides geohash encoding and decoding functions
for location-based channels and proximity-based routing.
"""

import math
from typing import Tuple, Optional

from ..exceptions import ValidationError
from ..constants import DEFAULT_GEOHASH_PRECISION


def encode_geohash(latitude: float, longitude: float, precision: int = DEFAULT_GEOHASH_PRECISION) -> str:
    """
    Encode latitude and longitude into a geohash.
    
    Args:
        latitude: Latitude in degrees
        longitude: Longitude in degrees
        precision: Number of characters in the geohash
        
    Returns:
        Geohash string
    """
    if not (-90.0 <= latitude <= 90.0) or not (-180.0 <= longitude <= 180.0):
        raise ValidationError("Invalid latitude or longitude")
    
    if precision < 1 or precision > 12:
        raise ValidationError("Precision must be between 1 and 12")
    
    # Define base32 characters
    base32_chars = "0123456789bcdefghjkmnpqrstuvwxyz"
    
    # Calculate bounds
    lat_range = [-90.0, 90.0]
    lon_range = [-180.0, 180.0]
    
    # Calculate hash
    geohash = ""
    is_even = True
    
    for i in range(precision * 5):
        # Divide range
        if is_even:
            # Longitude
            mid = (lon_range[0] + lon_range[1]) / 2
            if longitude >= mid:
                geohash += "1"
                lon_range[0] = mid
            else:
                geohash += "0"
                lon_range[1] = mid
        else:
            # Latitude
            mid = (lat_range[0] + lat_range[1]) / 2
            if latitude >= mid:
                geohash += "1"
                lat_range[0] = mid
            else:
                geohash += "0"
                lat_range[1] = mid
        
        is_even = not is_even
    
    # Convert binary to base32
    base32_geohash = ""
    for i in range(0, len(geohash), 5):
        byte = geohash[i:i+5]
        if len(byte) < 5:
            byte = byte.ljust(5, "0")
        base32_geohash += base32_chars[int(byte, 2)]
    
    return base32_geohash


def decode_geohash(geohash: str) -> Tuple[float, float]:
    """
    Decode a geohash into latitude and longitude.
    
    Args:
        geohash: Geohash string to decode
        
    Returns:
        Tuple of (latitude, longitude)
    """
    if not geohash:
        raise ValidationError("Geohash cannot be empty")
    
    # Define base32 characters
    base32_chars = "0123456789bcdefghjkmnpqrstuvwxyz"
    base32_map = {c: i for i, c in enumerate(base32_chars)}
    
    # Convert to binary
    binary = ""
    for c in geohash:
        if c not in base32_map:
            raise ValidationError(f"Invalid character in geohash: {c}")
        binary += format(base32_map[c], '05b')
    
    # Calculate bounds
    lat_range = [-90.0, 90.0]
    lon_range = [-180.0, 180.0]
    
    is_even = True
    for bit in binary:
        if is_even:
            # Longitude
            mid = (lon_range[0] + lon_range[1]) / 2
            if bit == "1":
                lon_range[0] = mid
            else:
                lon_range[1] = mid
        else:
            # Latitude
            mid = (lat_range[0] + lat_range[1]) / 2
            if bit == "1":
                lat_range[0] = mid
            else:
                lat_range[1] = mid
        
        is_even = not is_even
    
    # Calculate center of bounds
    lat = (lat_range[0] + lat_range[1]) / 2
    lon = (lon_range[0] + lon_range[1]) / 2
    
    return lat, lon


def get_neighbors(geohash: str) -> list:
    """
    Get all neighboring geohashes.
    
    Args:
        geohash: Geohash string
        
    Returns:
        List of neighboring geohashes
    """
    if not geohash:
        raise ValidationError("Geohash cannot be empty")
    
    # Decode the geohash to get the bounds
    lat, lon = decode_geohash(geohash)
    
    # Calculate the size of the geohash
    precision = len(geohash)
    lat_delta, lon_delta = _calculate_geohash_size(precision)
    
    # Calculate neighbor positions
    neighbors = []
    
    # North
    neighbors.append(encode_geohash(lat + lat_delta, lon, precision))
    
    # Northeast
    neighbors.append(encode_geohash(lat + lat_delta, lon + lon_delta, precision))
    
    # East
    neighbors.append(encode_geohash(lat, lon + lon_delta, precision))
    
    # Southeast
    neighbors.append(encode_geohash(lat - lat_delta, lon + lon_delta, precision))
    
    # South
    neighbors.append(encode_geohash(lat - lat_delta, lon, precision))
    
    # Southwest
    neighbors.append(encode_geohash(lat - lat_delta, lon - lon_delta, precision))
    
    # West
    neighbors.append(encode_geohash(lat, lon - lon_delta, precision))
    
    # Northwest
    neighbors.append(encode_geohash(lat + lat_delta, lon - lon_delta, precision))
    
    return neighbors


def _calculate_geohash_size(precision: int) -> Tuple[float, float]:
    """
    Calculate the approximate size of a geohash at a given precision.
    
    Args:
        precision: Geohash precision
        
    Returns:
        Tuple of (latitude_delta, longitude_delta)
    """
    # Approximate size based on precision
    # These are rough estimates
    lat_size = 180.0 / (2 ** (precision * 5 / 2))
    lon_size = 360.0 / (2 ** (precision * 5 / 2))
    
    return lat_size, lon_size


def get_current_geohash(precision: int = DEFAULT_GEOHASH_PRECISION) -> str:
    """
    Get the current geohash based on system location.
    
    Args:
        precision: Geohash precision
        
    Returns:
        Current geohash
    """
    try:
        # Try to get location from system
        # This is a placeholder - in a real implementation,
        # you would use a GPS module or IP geolocation
        import socket
        import requests
        
        # Get public IP
        ip = socket.gethostbyname(socket.gethostname())
        
        # Use IP geolocation service
        response = requests.get(f"http://ip-api.com/json/{ip}")
        data = response.json()
        
        if data.get("status") == "success":
            lat = data.get("lat", 0.0)
            lon = data.get("lon", 0.0)
            return encode_geohash(lat, lon, precision)
        else:
            # Return a default geohash if location detection fails
            return encode_geohash(0.0, 0.0, precision)
    
    except Exception:
        # Return a default geohash if location detection fails
        return encode_geohash(0.0, 0.0, precision)


def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate the distance between two points using the Haversine formula.
    
    Args:
        lat1: Latitude of first point
        lon1: Longitude of first point
        lat2: Latitude of second point
        lon2: Longitude of second point
        
    Returns:
        Distance in kilometers
    """
    # Convert to radians
    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)
    
    # Haversine formula
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad
    
    a = math.sin(dlat / 2) ** 2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a) / math.sqrt(1 - a))
    
    # Earth's radius in kilometers
    r = 6371.0
    
    return r * c


def is_within_radius(
    lat1: float, 
    lon1: float, 
    lat2: float, 
    lon2: float, 
    radius_km: float
) -> bool:
    """
    Check if a point is within a specified radius of another point.
    
    Args:
        lat1: Latitude of first point
        lon1: Longitude of first point
        lat2: Latitude of second point
        lon2: Longitude of second point
        radius_km: Radius in kilometers
        
    Returns:
        True if point2 is within radius of point1, False otherwise
    """
    distance = calculate_distance(lat1, lon1, lat2, lon2)
    return distance <= radius_km


def get_geohashes_in_radius(
    center_lat: float, 
    center_lon: float, 
    radius_km: float, 
    precision: int
) -> list:
    """
    Get all geohashes within a specified radius of a center point.
    
    Args:
        center_lat: Latitude of center point
        center_lon: Longitude of center point
        radius_km: Radius in kilometers
        precision: Geohash precision
        
    Returns:
        List of geohashes within the radius
    """
    # Get the center geohash
    center_geohash = encode_geohash(center_lat, center_lon, precision)
    
    # Start with the center geohash
    geohashes = [center_geohash]
    
    # Get neighbors
    neighbors = get_neighbors(center_geohash)
    geohashes.extend(neighbors)
    
    # Check if we need to include more neighbors
    # This is a simplified approach - a more sophisticated algorithm
    # would calculate the exact geohashes needed
    
    # Remove duplicates
    geohashes = list(set(geohashes))
    
    # Filter to only include geohashes within the radius
    result = []
    for geohash in geohashes:
        lat, lon = decode_geohash(geohash)
        if is_within_radius(center_lat, center_lon, lat, lon, radius_km):
            result.append(geohash)
    
    return result


def get_common_geohash_prefix(geohashes: list) -> str:
    """
    Get the common geohash prefix for a list of geohashes.
    
    Args:
        geohashes: List of geohash strings
        
    Returns:
        Common geohash prefix
    """
    if not geohashes:
        return ""
    
    # Find the shortest geohash
    min_length = min(len(geohash) for geohash in geohashes)
    
    # Find the common prefix
    common_prefix = ""
    
    for i in range(min_length):
        # Get the character at position i for all geohashes
        chars = set(geohash[i] for geohash in geohashes if i < len(geohash))
        
        # If all geohashes have the same character at this position, add it to the prefix
        if len(chars) == 1:
            common_prefix += list(chars)[0]
        else:
            # No common character at this position
            break
    
    return common_prefix