#!/usr/bin/env python3
"""
bitchat RPi 4 - Main Entry Point

This is the main entry point for the Blue Relay Chat RPi 4 client application.
It initializes the core components and starts the application.
"""

import asyncio
import signal
import sys
from pathlib import Path

from bitchat.core.controller import ApplicationController
from bitchat.config.manager import ConfigManager
from bitchat.utils.logging import setup_logging
from bitchat.exceptions import BitchatError


async def main() -> None:
    """Main application entry point."""
    # Setup logging first
    config_manager = ConfigManager()
    setup_logging(config_manager.get("application.log_level", "INFO"))
    
    logger = setup_logging(__name__)
    logger.info("Starting Blue Relay Chat RPi 4 client")
    
    try:
        # Initialize the application controller
        controller = ApplicationController(config_manager)
        
        # Setup signal handlers for graceful shutdown
        def signal_handler(signum, frame):
            logger.info(f"Received signal {signum}, initiating shutdown")
            asyncio.create_task(controller.shutdown())
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        # Start the application
        await controller.start()
        
        # Run the application until shutdown
        await controller.run()
        
    except BitchatError as e:
        logger.error(f"Application error: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt, shutting down")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)
    finally:
        logger.info("Application shutdown complete")


if __name__ == "__main__":
    # Check if we're running on a supported platform
    if not sys.platform.startswith("linux"):
        print("Error: Blue Relay Chat RPi 4 client requires Linux")
        sys.exit(1)
    
    # Run the main async function
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nShutdown complete")
        sys.exit(0)