"""
Utility modules for bitchat RPi 4 client.

This module provides various utility functions and classes used
throughout the application.
"""

from .logging import setup_logging, get_logger
from .geohash import encode_geohash, decode_geohash, get_current_geohash
from .compression import compress, decompress
from .helpers import generate_id, format_timestamp, sanitize_string
from .async_utils import create_task, gather_with_concurrency
from .hardware_detection import (
    get_hardware_detector,
    detect_hardware,
    get_hardware_profile,
    get_hardware_info,
)

__all__ = [
    "setup_logging",
    "get_logger",
    "encode_geohash",
    "decode_geohash",
    "get_current_geohash",
    "compress",
    "decompress",
    "generate_id",
    "format_timestamp",
    "sanitize_string",
    "create_task",
    "gather_with_concurrency",
    "get_hardware_detector",
    "detect_hardware",
    "get_hardware_profile",
    "get_hardware_info",
]