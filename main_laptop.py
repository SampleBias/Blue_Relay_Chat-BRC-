#!/usr/bin/env python3
"""
Main entry point for Blue Relay Chat laptop client.

This script provides a simple way to run the laptop client
with all components properly initialized and integrated.
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
    from bitchat.gui.laptop_gui import LaptopGUI
    from bitchat.core.events import EventBus
    from bitchat.core.laptop_controller import LaptopController
    from bitchat.utils.logging import setup_logging, get_logger
except ImportError as e:
    print(f"Error importing modules: {e}")
    sys.exit(1)


class LaptopClientApp:
    """Simple application wrapper for laptop client."""
    
    def __init__(self):
        """Initialize the application."""
        self.logger = get_logger("main")
        self.config = ConfigManager("config_laptop.ini")
        self.event_bus = EventBus()
        self.controller = LaptopController(self.config, self.event_bus)
        self.gui = LaptopGUI(self.config, self.event_bus)
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
            self.logger.info("Initializing laptop client application...")
            
            # Initialize controller
            await self.controller.initialize()
            
            # Set up component references
            self.controller.set_gui(self.gui)
            
            # Initialize GUI
            await self.gui.initialize()
            
            self.logger.info("Laptop client application initialized")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize application: {e}")
            raise
    
    async def start(self) -> None:
        """Start the application."""
        if self._running:
            self.logger.warning("Application is already running")
            return
        
        self._running = True
        self.logger.info("Starting laptop client application...")
        
        try:
            # Start controller
            await self.controller.start()
            
            # Start GUI
            await self.gui.start()
            
            self.logger.info("Laptop client application started")
            
            # Run main loop
            while self._running and not self._shutdown_requested:
                await asyncio.sleep(0.1)
            
            self.logger.info("Laptop client application stopped")
            
        except Exception as e:
            self.logger.error(f"Application error: {e}")
        finally:
            await self.stop()
    
    async def stop(self) -> None:
        """Stop the application."""
        if not self._running:
            self.logger.debug("Application is not running")
            return
        
        self._running = False
        self.logger.info("Stopping laptop client application...")
        
        try:
            # Stop GUI
            if self.gui:
                await self.gui.stop()
            
            # Stop controller
            if self.controller:
                await self.controller.stop()
            
            self.logger.info("Laptop client application stopped")
            
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
    logger.info("Starting Blue Relay Chat Laptop Client...")
    
    # Create and run application
    app = LaptopClientApp()
    
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