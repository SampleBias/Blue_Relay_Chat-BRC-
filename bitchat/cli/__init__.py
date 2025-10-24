"""
Command-line interface modules for Blue Relay Chat RPi 4 client.

This module provides CLI functionality including the main interface,
command parsing, display rendering, and UI components.
"""

from .interface import CLIInterface
from .commands import CommandProcessor
from .display import DisplayManager
from .widgets import WidgetManager

__all__ = ["CLIInterface", "CommandProcessor", "DisplayManager", "WidgetManager"]