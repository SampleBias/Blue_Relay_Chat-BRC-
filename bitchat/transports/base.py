"""
Base transport interface for Blue Relay Chat RPi 4 client.

This module provides the abstract base class that all transport
implementations must inherit from.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Callable
from enum import Enum

from ..config.manager import ConfigManager
from ..utils.logging import get_logger
from ..exceptions import TransportError
from ..constants import TransportType


class TransportStatus(Enum):
    """Transport status enumeration."""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    ERROR = "error"


class BaseTransport(ABC):
    """Abstract base class for all transport implementations."""
    
    def __init__(self, config_manager: ConfigManager, transport_type: TransportType) -> None:
        """
        Initialize the base transport.
        
        Args:
            config_manager: Configuration manager instance
            transport_type: Type of transport
        """
        self.config = config_manager
        self.transport_type = transport_type
        self.logger = get_logger(f"transport_{transport_type.value}")
        
        # Transport state
        self._status = TransportStatus.DISCONNECTED
        self._running = False
        
        # Event callbacks
        self._message_callback: Optional[Callable] = None
        self._status_callback: Optional[Callable] = None
        self._peer_callback: Optional[Callable] = None
    
    @property
    def status(self) -> TransportStatus:
        """Get the current transport status."""
        return self._status
    
    @property
    def is_connected(self) -> bool:
        """Check if the transport is connected."""
        return self._status == TransportStatus.CONNECTED
    
    @property
    def is_running(self) -> bool:
        """Check if the transport is running."""
        return self._running
    
    def set_message_callback(self, callback: Callable) -> None:
        """
        Set the callback for received messages.
        
        Args:
            callback: Callback function for received messages
        """
        self._message_callback = callback
    
    def set_status_callback(self, callback: Callable) -> None:
        """
        Set the callback for status changes.
        
        Args:
            callback: Callback function for status changes
        """
        self._status_callback = callback
    
    def set_peer_callback(self, callback: Callable) -> None:
        """
        Set the callback for peer events.
        
        Args:
            callback: Callback function for peer events
        """
        self._peer_callback = callback
    
    async def start(self) -> None:
        """Start the transport."""
        if self._running:
            self.logger.warning("Transport is already running")
            return
        
        try:
            self._running = True
            await self._set_status(TransportStatus.CONNECTING)
            await self._do_start()
            self.logger.info(f"{self.transport_type.value} transport started")
            
        except Exception as e:
            self.logger.error(f"Failed to start {self.transport_type.value} transport: {e}")
            await self._set_status(TransportStatus.ERROR)
            raise TransportError(f"Transport start failed: {e}")
    
    async def stop(self) -> None:
        """Stop the transport."""
        if not self._running:
            self.logger.debug("Transport is not running")
            return
        
        try:
            self._running = False
            await self._do_stop()
            await self._set_status(TransportStatus.DISCONNECTED)
            self.logger.info(f"{self.transport_type.value} transport stopped")
            
        except Exception as e:
            self.logger.error(f"Failed to stop {self.transport_type.value} transport: {e}")
            raise TransportError(f"Transport stop failed: {e}")
    
    async def send_message(self, message: Dict[str, Any]) -> bool:
        """
        Send a message through the transport.
        
        Args:
            message: Message to send
            
        Returns:
            True if message was sent successfully, False otherwise
        """
        if not self.is_connected:
            self.logger.warning(f"Cannot send message, {self.transport_type.value} transport not connected")
            return False
        
        try:
            return await self._do_send_message(message)
        except Exception as e:
            self.logger.error(f"Failed to send message via {self.transport_type.value}: {e}")
            return False
    
    async def get_connected_peers(self) -> Dict[str, Any]:
        """
        Get information about connected peers.
        
        Returns:
            Dictionary containing peer information
        """
        return await self._do_get_connected_peers()
    
    async def get_transport_info(self) -> Dict[str, Any]:
        """
        Get information about the transport.
        
        Returns:
            Dictionary containing transport information
        """
        return {
            "type": self.transport_type.value,
            "status": self._status.value,
            "running": self._running,
            "connected": self.is_connected,
        }
    
    @abstractmethod
    async def _do_start(self) -> None:
        """Start the transport implementation."""
        pass
    
    @abstractmethod
    async def _do_stop(self) -> None:
        """Stop the transport implementation."""
        pass
    
    @abstractmethod
    async def _do_send_message(self, message: Dict[str, Any]) -> bool:
        """Send a message implementation."""
        pass
    
    @abstractmethod
    async def _do_get_connected_peers(self) -> Dict[str, Any]:
        """Get connected peers implementation."""
        pass
    
    async def _set_status(self, status: TransportStatus) -> None:
        """
        Set the transport status and notify callbacks.
        
        Args:
            status: New transport status
        """
        old_status = self._status
        self._status = status
        
        if old_status != status:
            self.logger.debug(f"Transport status changed: {old_status.value} -> {status.value}")
            
            # Notify status callback
            if self._status_callback:
                try:
                    await self._status_callback(self.transport_type, status)
                except Exception as e:
                    self.logger.error(f"Error in status callback: {e}")
    
    async def _on_message_received(self, message: Dict[str, Any]) -> None:
        """
        Handle a received message.
        
        Args:
            message: Received message
        """
        self.logger.debug(f"Message received via {self.transport_type.value}")
        
        # Notify message callback
        if self._message_callback:
            try:
                await self._message_callback(message, self.transport_type)
            except Exception as e:
                self.logger.error(f"Error in message callback: {e}")
    
    async def _on_peer_connected(self, peer_id: str, peer_info: Dict[str, Any]) -> None:
        """
        Handle a peer connection event.
        
        Args:
            peer_id: ID of the connected peer
            peer_info: Information about the peer
        """
        self.logger.debug(f"Peer connected via {self.transport_type.value}: {peer_id}")
        
        # Notify peer callback
        if self._peer_callback:
            try:
                await self._peer_callback("connected", peer_id, peer_info, self.transport_type)
            except Exception as e:
                self.logger.error(f"Error in peer callback: {e}")
    
    async def _on_peer_disconnected(self, peer_id: str, peer_info: Dict[str, Any]) -> None:
        """
        Handle a peer disconnection event.
        
        Args:
            peer_id: ID of the disconnected peer
            peer_info: Information about the peer
        """
        self.logger.debug(f"Peer disconnected via {self.transport_type.value}: {peer_id}")
        
        # Notify peer callback
        if self._peer_callback:
            try:
                await self._peer_callback("disconnected", peer_id, peer_info, self.transport_type)
            except Exception as e:
                self.logger.error(f"Error in peer callback: {e}")
    
    async def _on_error(self, error: Exception) -> None:
        """
        Handle a transport error.
        
        Args:
            error: The error that occurred
        """
        self.logger.error(f"Transport error in {self.transport_type.value}: {error}")
        await self._set_status(TransportStatus.ERROR)