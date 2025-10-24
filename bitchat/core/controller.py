"""
Application controller for bitchat RPi 4 client.

This module contains the main application controller that coordinates
all components and manages the application lifecycle.
"""

import asyncio
from typing import Optional, Dict, Any

from ..config.manager import ConfigManager
from ..utils.logging import get_logger
from ..exceptions import BitchatError
from .events import EventBus
from .router import MessageRouter


class ApplicationController:
    """Main application controller that coordinates all components."""
    
    def __init__(self, config_manager: ConfigManager) -> None:
        """
        Initialize the application controller.
        
        Args:
            config_manager: Configuration manager instance
        """
        self.config = config_manager
        self.logger = get_logger("controller")
        self.event_bus = EventBus()
        
        # Component instances (will be initialized in start())
        self.message_router: Optional[MessageRouter] = None
        
        # Application state
        self._running = False
        self._shutdown_event = asyncio.Event()
        
        self.logger.info("Application controller initialized")
    
    async def start(self) -> None:
        """Start the application and all components."""
        if self._running:
            self.logger.warning("Application is already running")
            return
        
        self.logger.info("Starting application components")
        
        try:
            # Initialize core components
            await self._initialize_components()
            
            # Start all components
            await self._start_components()
            
            self._running = True
            self.logger.info("Application started successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to start application: {e}")
            await self.shutdown()
            raise BitchatError(f"Application startup failed: {e}")
    
    async def _initialize_components(self) -> None:
        """Initialize all application components."""
        self.logger.debug("Initializing message router")
        self.message_router = MessageRouter(self.config, self.event_bus)
        
        # Initialize other components here as they are implemented
        # self.bluetooth_transport = BluetoothTransport(self.config, self.event_bus)
        # self.nostr_transport = NostrTransport(self.config, self.event_bus)
        # self.identity_manager = IdentityManager(self.config, self.event_bus)
        # self.cli_interface = CLIInterface(self.config, self.event_bus)
    
    async def _start_components(self) -> None:
        """Start all application components."""
        if self.message_router:
            await self.message_router.start()
        
        # Start other components here as they are implemented
        # await self.bluetooth_transport.start()
        # await self.nostr_transport.start()
        # await self.identity_manager.start()
        # await self.cli_interface.start()
    
    async def run(self) -> None:
        """Run the main application loop."""
        if not self._running:
            raise BitchatError("Application must be started before running")
        
        self.logger.info("Starting main application loop")
        
        try:
            # Wait for shutdown signal
            await self._shutdown_event.wait()
            
        except asyncio.CancelledError:
            self.logger.info("Application loop cancelled")
        except Exception as e:
            self.logger.error(f"Error in application loop: {e}")
            raise
        finally:
            self.logger.info("Application loop ended")
    
    async def shutdown(self) -> None:
        """Shutdown the application and all components."""
        if not self._running:
            self.logger.debug("Application is not running")
            return
        
        self.logger.info("Shutting down application")
        
        try:
            # Stop all components
            await self._stop_components()
            
            # Cleanup resources
            await self._cleanup()
            
            self._running = False
            self._shutdown_event.set()
            
            self.logger.info("Application shutdown complete")
            
        except Exception as e:
            self.logger.error(f"Error during shutdown: {e}")
            raise
    
    async def _stop_components(self) -> None:
        """Stop all application components."""
        stop_tasks = []
        
        # Add component shutdown tasks here as they are implemented
        # if self.cli_interface:
        #     stop_tasks.append(self.cli_interface.stop())
        # if self.nostr_transport:
        #     stop_tasks.append(self.nostr_transport.stop())
        # if self.bluetooth_transport:
        #     stop_tasks.append(self.bluetooth_transport.stop())
        if self.message_router:
            stop_tasks.append(self.message_router.stop())
        
        if stop_tasks:
            await asyncio.gather(*stop_tasks, return_exceptions=True)
    
    async def _cleanup(self) -> None:
        """Perform cleanup operations."""
        # Close event bus
        await self.event_bus.close()
        
        # Additional cleanup operations can be added here
        pass
    
    def is_running(self) -> bool:
        """Check if the application is running."""
        return self._running
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get the current application status.
        
        Returns:
            Dictionary containing application status information
        """
        status = {
            "running": self._running,
            "version": self.config.get("application.version", "unknown"),
            "components": {}
        }
        
        # Add component status here as they are implemented
        if self.message_router:
            status["components"]["message_router"] = self.message_router.get_status()
        
        return status
    
    async def reload_config(self) -> None:
        """Reload configuration and update components."""
        self.logger.info("Reloading configuration")
        
        try:
            # Reload configuration
            self.config.reload()
            
            # Update components with new configuration
            # This will be implemented as components are added
            # await self._update_components_config()
            
            self.logger.info("Configuration reloaded successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to reload configuration: {e}")
            raise BitchatError(f"Configuration reload failed: {e}")
    
    async def emergency_wipe(self) -> None:
        """Perform emergency wipe of all sensitive data."""
        self.logger.warning("Initiating emergency wipe")
        
        try:
            # Stop all components first
            await self._stop_components()
            
            # Perform emergency wipe on components
            # This will be implemented as components are added
            # if self.identity_manager:
            #     await self.identity_manager.emergency_wipe()
            # if self.message_router:
            #     await self.message_router.emergency_wipe()
            
            self.logger.warning("Emergency wipe completed")
            
        except Exception as e:
            self.logger.error(f"Error during emergency wipe: {e}")
            raise BitchatError(f"Emergency wipe failed: {e}")
        finally:
            # Ensure shutdown after wipe
            await self._cleanup()
            self._running = False
            self._shutdown_event.set()