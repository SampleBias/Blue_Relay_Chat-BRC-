#!/usr/bin/env python3
"""
Standalone script to run small screen GUI.

This script provides a simple way to run the small screen GUI
without module import issues.
"""

import asyncio
import os
import sys
import signal
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

try:
    from bitchat.config.manager import ConfigManager
    from bitchat.core.events import EventBus
    from bitchat.gui.small_screen_gui import SmallScreenGUI
    from bitchat.utils.logging import setup_logging, get_logger
except ImportError as e:
    print(f"Error importing modules: {e}")
    sys.exit(1)


class SmallScreenApp:
    """Simple application wrapper for small screen GUI."""
    
    def __init__(self) -> None:
        """Initialize application."""
        self.logger = get_logger("main")
        self.config = ConfigManager()
        self.event_bus = EventBus()
        self.gui: Optional[SmallScreenGUI] = None
        self._running = False
        self._shutdown_requested = False
        
        # Set up signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame) -> None:
        """Handle system signals."""
