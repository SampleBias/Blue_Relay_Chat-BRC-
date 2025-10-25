#!/usr/bin/env python3
"""
Main entry point for Blue Relay Chat with small screen GUI.

This script provides a simple way to run the small screen GUI
without the full application framework.
"""

import asyncio
import sys
import os
import signal
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

try:
    from bitchat.config.manager import ConfigManager
    from bitchat.gui.small_screen_gui import SmallScreenGUI
    from bitchat.core.events import EventBus
    from bitchat.utils.logging import setup_logging, get_logger
except ImportError as e:
    print(f"Error importing modules: {e}")
    sys.exit(1)


class SmallScreenApp:
    """Simple application wrapper for small screen GUI."""
    
    def __init__(self) -> None:
        """Initialize the application."""
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
        self.logger.info(f"Received signal {signum}, shutting down...")
        self._shutdown_requested = True
    
    async def initialize(self) -> None:
        """Initialize the application components."""
        try:
            self.logger.info("Initializing small screen GUI application...")
            
            # Initialize GUI
            self.gui = SmallScreenGUI(self.config, self.event_bus)
            await self.gui.initialize()
            
            self.logger.info("Small screen GUI application initialized")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize application: {e}")
            raise
    
    async def start(self) -> None:
        """Start the application."""
        if self._running:
            self.logger.warning("Application is already running")
            return
        
        self._running = True
        self.logger.info("Starting small screen GUI application...")
        
        try:
            # Start GUI
            await self.gui.start()
            
            self.logger.info("Small screen GUI application started")
            
            # Run main loop
            while self._running and not self._shutdown_requested:
                await asyncio.sleep(1)
            
            self.logger.info("Small screen GUI application stopped")
            
        except Exception as e:
            self.logger.error(f"Application error: {e}")
        finally:
            await self.stop()
    
    async def stop(self) -> None:
        """Stop the application."""
        if not self._running:
            return
        
        self._running = False
        self.logger.info("Stopping small screen GUI application...")
        
        try:
            if self.gui:
                await self.gui.stop()
            
            self.logger.info("Small screen GUI application stopped")
            
        except Exception as e:
            self.logger.error(f"Error stopping application: {e}")


async def main() -> None:
    """Main entry point."""
    # Set up logging
    setup_logging(
        level="INFO",
        log_file=None,
        console_output=True
    )
    
    logger = get_logger("main")
    logger.info("Starting Blue Relay Chat Small Screen GUI...")
    
    # Create and initialize application
    app = SmallScreenApp()
    
    try:
        await app.initialize()
        await app.start()
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt, shutting down...")
    except Exception as e:
        logger.error(f"Application error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    # Run the application
    asyncio.run(main())