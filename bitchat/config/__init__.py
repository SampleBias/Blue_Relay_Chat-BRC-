"""
Configuration management module for bitchat RPi 4 client.

This module provides configuration management functionality including
loading, validation, and access to application settings.
"""

from .manager import ConfigManager
from .defaults import DEFAULT_CONFIG
from .validation import ConfigValidator

__all__ = ["ConfigManager", "DEFAULT_CONFIG", "ConfigValidator"]