"""
Laptop controller for Blue Relay Chat client.

This module coordinates all components and manages the application
lifecycle for the laptop client implementation.
"""

import asyncio
from typing import Optional, Dict, Any

from ..config.manager import ConfigManager
from ..core.events import EventBus, Event, EventTypes
from ..utils.logging import get_logger


class LaptopController:
    """Main controller for Blue Relay Chat laptop client."""
    
    def __init__(self, config_manager: ConfigManager, event_bus: EventBus):
        """
        Initialize the laptop controller.
        
        Args:
            config_manager: Configuration manager instance
            event_bus: Event bus for component communication
        """
        self.config = config_manager
        self.event_bus = event_bus
        self.logger = get_logger("laptop_controller")
        
        # Component references (will be initialized in start())
        self.message_router: Optional = None
        self.bluetooth_transport: Optional = None
        self.crypto_service: Optional = None
        self.identity_manager: Optional = None
        self.database_service: Optional = None
        self.gui: Optional = None
        
        # Application state
        self._running = False
        self._initialized = False
        
        # Set application mode to laptop
        config_manager.set("application.mode", "laptop")
        
        self.logger.info("Laptop controller initialized")
    
    async def initialize(self) -> None:
        """Initialize all application components."""
        if self._initialized:
            self.logger.warning("Controller already initialized")
            return
        
        self.logger.info("Initializing laptop controller components...")
        
        try:
            # Import and initialize core components
            from ..core.router import MessageRouter
            from ..security.crypto import CryptoService
            from ..security.identity import IdentityManager
            from ..data.database import DatabaseService
            
            # Initialize core components
            self.message_router = MessageRouter(self.config, self.event_bus)
            await self.message_router.start()
            
            self.crypto_service = CryptoService(self.config)
            self.identity_manager = IdentityManager(self.config, self.event_bus)
            await self.identity_manager.initialize()
            
            self.database_service = DatabaseService(self.config)
            
            # Import and initialize Bluetooth transport
            from ..transports.laptop_bluetooth import LaptopBluetoothTransport
            
            self.bluetooth_transport = LaptopBluetoothTransport(self.config)
            
            self.logger.info("Core components initialized")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize components: {e}")
            raise
    
    async def start(self) -> None:
        """Start the laptop controller and all components."""
        if self._running:
            self.logger.warning("Controller is already running")
            return
        
        if not self._initialized:
            raise RuntimeError("Controller must be initialized before starting")
        
        self._running = True
        self.logger.info("Starting laptop controller...")
        
        try:
            # Start Bluetooth transport
            if self.bluetooth_transport:
                await self.bluetooth_transport.start()
                
                # Register with message router
                await self.message_router.register_transport(self.bluetooth_transport)
            
            # Publish controller started event
            await self.event_bus.publish(Event(
                type=EventTypes.SYSTEM_STARTUP,
                data={"component": "laptop_controller"},
                source="laptop_controller"
            ))
            
            self.logger.info("Laptop controller started successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to start controller: {e}")
            await self.shutdown()
            raise
    
    async def stop(self) -> None:
        """Stop the laptop controller and all components."""
        if not self._running:
            self.logger.debug("Controller is not running")
            return
        
        self._running = False
        self.logger.info("Stopping laptop controller...")
        
        try:
            # Stop Bluetooth transport
            if self.bluetooth_transport:
                await self.bluetooth_transport.stop()
            
            # Stop message router
            if self.message_router:
                await self.message_router.stop()
            
            # Stop identity manager
            if self.identity_manager:
                await self.identity_manager.stop()
            
            # Close database service
            if self.database_service and self.database_service.connection:
                await self.database_service.connection.close()
            
            # Publish controller stopped event
            await self.event_bus.publish(Event(
                type=EventTypes.SYSTEM_SHUTDOWN,
                data={"component": "laptop_controller"},
                source="laptop_controller"
            ))
            
            self.logger.info("Laptop controller stopped")
            
        except Exception as e:
            self.logger.error(f"Error during controller shutdown: {e}")
            raise
    
    def set_gui(self, gui) -> None:
        """Set the GUI reference."""
        self.gui = gui
        
        # Set up GUI event handlers
        if self.gui:
            self.gui.set_controller(self)
    
    def set_message_router(self, message_router) -> None:
        """Set the message router reference."""
        self.message_router = message_router
    
    def set_crypto_service(self, crypto_service) -> None:
        """Set the crypto service reference."""
        self.crypto_service = crypto_service
    
    def set_identity_manager(self, identity_manager) -> None:
        """Set the identity manager reference."""
        self.identity_manager = identity_manager
    
    def set_database_service(self, database_service) -> None:
        """Set the database service reference."""
        self.database_service = database_service
    
    async def send_message(self, content: str, recipient_id: Optional[str] = None, 
                    channel_id: Optional[str] = None) -> bool:
        """
        Send a message through the appropriate transport.
        
        Args:
            content: Message content
            recipient_id: Optional recipient for direct message
            channel_id: Optional channel for channel message
            
        Returns:
            True if message was sent successfully, False otherwise
        """
        try:
            if not self._running:
                self.logger.warning("Controller is not running, cannot send message")
                return False
            
            # Create message object
            message = {
                "content": content,
                "type": "text",
                "sender": await self.identity_manager.get_display_name(),
                "timestamp": asyncio.get_event_loop().time()
            }
            
            # Add recipient or channel
            if recipient_id:
                message["recipient_id"] = recipient_id
            if channel_id:
                message["channel_id"] = channel_id
            
            # Send through message router
            if self.message_router:
                return await self.message_router.route_message(message)
            else:
                self.logger.warning("Message router not available, cannot send message")
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to send message: {e}")
            return False
    
    async def join_channel(self, channel_id: str) -> bool:
        """
        Join a specific channel.
        
        Args:
            channel_id: Channel identifier to join
            
        Returns:
            True if joined successfully, False otherwise
        """
        try:
            if not self._running:
                self.logger.warning("Controller is not running, cannot join channel")
                return False
            
            # Create channel join message
            message = {
                "content": f"Joined channel: {channel_id}",
                "type": "system",
                "channel_id": channel_id,
                "sender": "System"
            }
            
            # Send through message router
            if self.message_router:
                result = await self.message_router.route_message(message)
                
                # Update current channel in GUI
                if result and self.gui:
                    self.gui._current_channel = channel_id
                    await self.gui.event_bus.publish(Event(
                        type=EventTypes.CHANNEL_JOINED,
                        data={"channel_id": channel_id},
                        source="laptop_controller"
                    ))
                
                return result
            else:
                self.logger.warning("Message router not available, cannot join channel")
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to join channel: {e}")
            return False
    
    async def get_connected_peers(self) -> Dict[str, Any]:
        """
        Get information about connected peers.
        
        Returns:
            Dictionary of connected peers with their information
        """
        try:
            if self.bluetooth_transport:
                return await self.bluetooth_transport.get_connected_peers()
            else:
                return {}
                
        except Exception as e:
            self.logger.error(f"Failed to get connected peers: {e}")
            return {}
    
    async def get_status(self) -> Dict[str, Any]:
        """
        Get the current status of the application.
        
        Returns:
            Dictionary containing status information
        """
        try:
            status = {
                "running": self._running,
                "initialized": self._initialized,
                "transport_status": {},
                "connected_peers": 0,
                "current_channel": self.gui._current_channel if self.gui else None
            }
            
            # Get transport status
            if self.bluetooth_transport:
                transport_status = await self.bluetooth_transport.get_status()
                status["transport_status"] = transport_status
            
            # Get connected peers count
            connected_peers = await self.get_connected_peers()
            status["connected_peers"] = len(connected_peers)
            
            return status
            
        except Exception as e:
            self.logger.error(f"Failed to get status: {e}")
            return {"running": False, "error": str(e)}
    
    def is_running(self) -> bool:
        """Check if the controller is running."""
        return self._running
    
    def is_initialized(self) -> bool:
        """Check if the controller is initialized."""
        return self._initialized