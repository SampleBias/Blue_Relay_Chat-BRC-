"""
Nostr protocol transport implementation for Blue Relay Chat RPi 4 client.

This module provides the Nostr protocol implementation for global
communication using Nostr relays and the WebSocket protocol.
"""

import asyncio
import json
import time
from typing import Dict, Any, Optional, List, Set
from datetime import datetime

import websockets
from websockets.client import WebSocketClientProtocol

from ...config.manager import ConfigManager
from ...utils.logging import get_logger
from ...constants import TransportType
from ...exceptions import NostrError, TransportError
from ...security.crypto import CryptoManager
from ..base import BaseTransport, TransportStatus
from .events import NostrEventManager
from .relay_manager import RelayManager
from .nips.nip01 import BasicProtocol
from .nips.nip04 import Encryption
from .nips.nip17 import GiftWraps


class NostrTransport(BaseTransport):
    """Nostr protocol transport implementation."""
    
    def __init__(self, config_manager: ConfigManager) -> None:
        """
        Initialize the Nostr transport.
        
        Args:
            config_manager: Configuration manager instance
        """
        super().__init__(config_manager, TransportType.NOSTR)
        
        # Nostr configuration
        self.relays = config_manager.get_nostr_relays()
        self.max_relay_connections = config_manager.get("nostr.max_relay_connections", 5)
        self.subscription_limit = config_manager.get("nostr.subscription_limit", 10)
        self.event_batch_size = config_manager.get("nostr.event_batch_size", 50)
        self.connection_timeout = config_manager.get("nostr.connection_timeout_seconds", 15)
        self.reconnect_interval = config_manager.get("nostr.reconnect_interval_seconds", 30)
        
        # Nostr components
        self.crypto_manager = CryptoManager(config_manager)
        self.event_manager = NostrEventManager(config_manager)
        self.relay_manager = RelayManager(config_manager)
        self.basic_protocol = BasicProtocol()
        self.encryption = Encryption(self.crypto_manager)
        self.gift_wraps = GiftWraps(self.crypto_manager)
        
        # Connection state
        self._connected_relays: Dict[str, WebSocketClientProtocol] = {}
        self._relay_subscriptions: Dict[str, Set[str]] = {}
        self._subscription_filters: Dict[str, Dict[str, Any]] = {}
        self._connection_tasks: Dict[str, asyncio.Task] = {}
        
        # Event handling
        self._event_handlers: Dict[int, callable] = {}
        self._next_event_id = 1
    
    async def _do_start(self) -> None:
        """Start the Nostr transport."""
        try:
            # Initialize event manager
            await self.event_manager.initialize()
            
            # Connect to relays
            await self._connect_to_relays()
            
            # Set up event handlers
            self._setup_event_handlers()
            
            await self._set_status(TransportStatus.CONNECTED)
            self.logger.info("Nostr transport started successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to start Nostr transport: {e}")
            raise NostrError(f"Nostr transport start failed: {e}")
    
    async def _do_stop(self) -> None:
        """Stop the Nostr transport."""
        try:
            # Disconnect from all relays
            await self._disconnect_from_relays()
            
            # Stop event manager
            await self.event_manager.stop()
            
            self.logger.info("Nostr transport stopped")
            
        except Exception as e:
            self.logger.error(f"Failed to stop Nostr transport: {e}")
            raise NostrError(f"Nostr transport stop failed: {e}")
    
    async def _do_send_message(self, message: Dict[str, Any]) -> bool:
        """Send a message via Nostr."""
        try:
            # Create Nostr event
            event = await self._create_nostr_event(message)
            
            if not event:
                return False
            
            # Send event to all connected relays
            success_count = 0
            for relay_url, websocket in self._connected_relays.items():
                try:
                    await self._send_event_to_relay(websocket, event)
                    success_count += 1
                except Exception as e:
                    self.logger.error(f"Failed to send event to relay {relay_url}: {e}")
            
            return success_count > 0
            
        except Exception as e:
            self.logger.error(f"Failed to send Nostr message: {e}")
            return False
    
    async def _do_get_connected_peers(self) -> Dict[str, Any]:
        """Get information about connected Nostr relays."""
        relays = {}
        
        for relay_url in self._connected_relays:
            relays[relay_url] = {
                "url": relay_url,
                "connected": True,
                "subscriptions": len(self._relay_subscriptions.get(relay_url, set())),
                "last_activity": "unknown",  # Could be tracked if needed
            }
        
        return {
            "total_relays": len(self.relays),
            "connected_relays": len(self._connected_relays),
            "max_relays": self.max_relay_connections,
            "relays": relays,
        }
    
    async def _connect_to_relays(self) -> None:
        """Connect to Nostr relays."""
        # Limit connections to max_relay_connections
        relay_urls = self.relays[:self.max_relay_connections]
        
        connection_tasks = []
        for relay_url in relay_urls:
            task = asyncio.create_task(self._connect_to_relay(relay_url))
            connection_tasks.append(task)
            self._connection_tasks[relay_url] = task
        
        # Wait for all connections (with timeout)
        try:
            await asyncio.wait_for(
                asyncio.gather(*connection_tasks, return_exceptions=True),
                timeout=self.connection_timeout
            )
        except asyncio.TimeoutError:
            self.logger.warning("Some relay connections timed out")
    
    async def _connect_to_relay(self, relay_url: str) -> None:
        """Connect to a single Nostr relay."""
        try:
            # Create WebSocket connection
            websocket = await websockets.connect(
                relay_url,
                timeout=self.connection_timeout,
                ping_interval=20,
                ping_timeout=10
            )
            
            # Store connection
            self._connected_relays[relay_url] = websocket
            self._relay_subscriptions[relay_url] = set()
            
            # Start message handler for this relay
            asyncio.create_task(self._handle_relay_messages(relay_url, websocket))
            
            self.logger.info(f"Connected to Nostr relay: {relay_url}")
            
        except Exception as e:
            self.logger.error(f"Failed to connect to relay {relay_url}: {e}")
            # Schedule reconnection attempt
            asyncio.create_task(self._schedule_reconnect(relay_url))
    
    async def _disconnect_from_relays(self) -> None:
        """Disconnect from all Nostr relays."""
        # Cancel connection tasks
        for relay_url, task in self._connection_tasks.items():
            if not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
        
        self._connection_tasks.clear()
        
        # Close WebSocket connections
        close_tasks = []
        for relay_url, websocket in self._connected_relays.items():
            task = asyncio.create_task(self._close_relay_connection(relay_url, websocket))
            close_tasks.append(task)
        
        if close_tasks:
            await asyncio.gather(*close_tasks, return_exceptions=True)
        
        self._connected_relays.clear()
        self._relay_subscriptions.clear()
    
    async def _close_relay_connection(self, relay_url: str, websocket: WebSocketClientProtocol) -> None:
        """Close connection to a relay."""
        try:
            await websocket.close()
            self.logger.debug(f"Closed connection to relay: {relay_url}")
        except Exception as e:
            self.logger.error(f"Error closing connection to relay {relay_url}: {e}")
    
    async def _handle_relay_messages(self, relay_url: str, websocket: WebSocketClientProtocol) -> None:
        """Handle messages from a relay."""
        try:
            async for message in websocket:
                try:
                    # Parse JSON message
                    data = json.loads(message)
                    
                    # Handle different message types
                    if isinstance(data, list) and len(data) >= 2:
                        message_type = data[0]
                        
                        if message_type == "EVENT":
                            # Handle event message
                            await self._handle_event_message(relay_url, data)
                        elif message_type == "EOSE":
                            # Handle end of stored events
                            await self._handle_eose_message(relay_url, data)
                        elif message_type == "OK":
                            # Handle OK message (event acceptance)
                            await self._handle_ok_message(relay_url, data)
                        elif message_type == "NOTICE":
                            # Handle notice message
                            await self._handle_notice_message(relay_url, data)
                    
                except json.JSONDecodeError as e:
                    self.logger.error(f"Invalid JSON from relay {relay_url}: {e}")
                except Exception as e:
                    self.logger.error(f"Error handling message from relay {relay_url}: {e}")
        
        except websockets.exceptions.ConnectionClosed:
            self.logger.warning(f"Connection to relay {relay_url} closed")
            await self._handle_relay_disconnection(relay_url)
        except Exception as e:
            self.logger.error(f"Error in relay message handler for {relay_url}: {e}")
            await self._handle_relay_disconnection(relay_url)
    
    async def _handle_event_message(self, relay_url: str, data: List) -> None:
        """Handle an EVENT message from a relay."""
        try:
            if len(data) < 3:
                return
            
            subscription_id = data[1]
            event_data = data[2]
            
            # Validate event
            if not self.basic_protocol.validate_event(event_data):
                self.logger.warning(f"Invalid event received from relay {relay_url}")
                return
            
            # Process event
            await self.event_manager.process_event(event_data)
            
            # Check if this is a message event
            if event_data.get("kind") == 1:  # Text note
                await self._handle_text_note_event(event_data)
            elif event_data.get("kind") == 4:  # Encrypted direct message
                await self._handle_encrypted_dm_event(event_data)
            elif event_data.get("kind") == 1059:  # Gift wrap
                await self._handle_gift_wrap_event(event_data)
            
        except Exception as e:
            self.logger.error(f"Error handling event message: {e}")
    
    async def _handle_text_note_event(self, event_data: Dict[str, Any]) -> None:
        """Handle a text note event."""
        try:
            # Extract content
            content = event_data.get("content", "")
            author = event_data.get("pubkey", "")
            created_at = event_data.get("created_at", 0)
            
            # Create message
            message = {
                "id": event_data.get("id"),
                "sender_id": author,
                "content": content,
                "timestamp": datetime.fromtimestamp(created_at).isoformat(),
                "transport_type": "nostr",
                "event_data": event_data,
            }
            
            # Handle the message
            await self._on_message_received(message)
            
        except Exception as e:
            self.logger.error(f"Error handling text note event: {e}")
    
    async def _handle_encrypted_dm_event(self, event_data: Dict[str, Any]) -> None:
        """Handle an encrypted direct message event."""
        try:
            # Extract content
            content = event_data.get("content", "")
            author = event_data.get("pubkey", "")
            
            # Decrypt content
            decrypted_content = await self.encryption.decrypt_dm(content, author)
            
            if decrypted_content:
                # Create message
                message = {
                    "id": event_data.get("id"),
                    "sender_id": author,
                    "content": decrypted_content,
                    "transport_type": "nostr",
                    "encrypted": True,
                    "event_data": event_data,
                }
                
                # Handle the message
                await self._on_message_received(message)
            
        except Exception as e:
            self.logger.error(f"Error handling encrypted DM event: {e}")
    
    async def _handle_gift_wrap_event(self, event_data: Dict[str, Any]) -> None:
        """Handle a gift wrap event."""
        try:
            # Extract content
            content = event_data.get("content", "")
            author = event_data.get("pubkey", "")
            
            # Unwrap gift
            unwrapped_event = await self.gift_wraps.unwrap_gift(content, author)
            
            if unwrapped_event:
                # Process the unwrapped event
                await self._handle_event_message("gift_wrap", ["EVENT", "gift_wrap", unwrapped_event])
            
        except Exception as e:
            self.logger.error(f"Error handling gift wrap event: {e}")
    
    async def _handle_eose_message(self, relay_url: str, data: List) -> None:
        """Handle an EOSE (End of Stored Events) message."""
        subscription_id = data[1] if len(data) > 1 else ""
        self.logger.debug(f"Received EOSE for subscription {subscription_id} from {relay_url}")
    
    async def _handle_ok_message(self, relay_url: str, data: List) -> None:
        """Handle an OK message (event acceptance)."""
        if len(data) < 3:
            return
        
        event_id = data[1]
        success = data[2] == True
        message = data[3] if len(data) > 3 else ""
        
        if success:
            self.logger.debug(f"Event {event_id} accepted by relay {relay_url}")
        else:
            self.logger.warning(f"Event {event_id} rejected by relay {relay_url}: {message}")
    
    async def _handle_notice_message(self, relay_url: str, data: List) -> None:
        """Handle a NOTICE message from a relay."""
        message = data[1] if len(data) > 1 else ""
        self.logger.info(f"Notice from relay {relay_url}: {message}")
    
    async def _handle_relay_disconnection(self, relay_url: str) -> None:
        """Handle disconnection from a relay."""
        # Remove from connected relays
        self._connected_relays.pop(relay_url, None)
        self._relay_subscriptions.pop(relay_url, None)
        
        # Cancel connection task
        if relay_url in self._connection_tasks:
            task = self._connection_tasks.pop(relay_url)
            if not task.done():
                task.cancel()
        
        # Schedule reconnection
        await self._schedule_reconnect(relay_url)
    
    async def _schedule_reconnect(self, relay_url: str) -> None:
        """Schedule reconnection to a relay."""
        try:
            await asyncio.sleep(self.reconnect_interval)
            
            if self._running and relay_url not in self._connected_relays:
                self.logger.info(f"Attempting to reconnect to relay: {relay_url}")
                await self._connect_to_relay(relay_url)
        
        except asyncio.CancelledError:
            pass
        except Exception as e:
            self.logger.error(f"Error during reconnect to {relay_url}: {e}")
    
    async def _create_nostr_event(self, message: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create a Nostr event from a message."""
        try:
            # Get identity information
            # This would come from the identity manager
            private_key = "placeholder"  # Would be retrieved from identity manager
            public_key = "placeholder"   # Would be retrieved from identity manager
            
            # Determine event kind
            recipient_id = message.get("recipient_id")
            if recipient_id:
                # Encrypted direct message
                kind = 4
                content = await self.encryption.encrypt_dm(
                    message.get("content", ""),
                    recipient_id,
                    private_key
                )
                tags = [["p", recipient_id]]
            else:
                # Text note
                kind = 1
                content = message.get("content", "")
                tags = []
                
                # Add channel tag if present
                channel_id = message.get("channel_id")
                if channel_id:
                    tags.append(["t", channel_id])
            
            # Create event
            event = {
                "kind": kind,
                "created_at": int(time.time()),
                "content": content,
                "tags": tags,
                "pubkey": public_key,
            }
            
            # Sign event
            event["id"] = self.basic_protocol.get_event_id(event)
            event["sig"] = self.basic_protocol.sign_event(event, private_key)
            
            return event
            
        except Exception as e:
            self.logger.error(f"Failed to create Nostr event: {e}")
            return None
    
    async def _send_event_to_relay(self, websocket: WebSocketClientProtocol, event: Dict[str, Any]) -> None:
        """Send an event to a relay."""
        message = ["EVENT", event]
        await websocket.send(json.dumps(message))
    
    async def subscribe_to_events(self, filters: Dict[str, Any]) -> str:
        """
        Subscribe to events from relays.
        
        Args:
            filters: Nostr filter dictionary
            
        Returns:
            Subscription ID
        """
        subscription_id = f"sub_{self._next_event_id}"
        self._next_event_id += 1
        
        # Store subscription filters
        self._subscription_filters[subscription_id] = filters
        
        # Send subscription to all connected relays
        message = ["REQ", subscription_id, filters]
        
        for relay_url, websocket in self._connected_relays.items():
            try:
                await websocket.send(json.dumps(message))
                self._relay_subscriptions[relay_url].add(subscription_id)
            except Exception as e:
                self.logger.error(f"Failed to send subscription to relay {relay_url}: {e}")
        
        return subscription_id
    
    async def unsubscribe_from_events(self, subscription_id: str) -> None:
        """
        Unsubscribe from events.
        
        Args:
            subscription_id: Subscription ID to cancel
        """
        # Remove from filters
        self._subscription_filters.pop(subscription_id, None)
        
        # Send unsubscription to all connected relays
        message = ["CLOSE", subscription_id]
        
        for relay_url, websocket in self._connected_relays.items():
            try:
                if subscription_id in self._relay_subscriptions[relay_url]:
                    await websocket.send(json.dumps(message))
                    self._relay_subscriptions[relay_url].remove(subscription_id)
            except Exception as e:
                self.logger.error(f"Failed to send unsubscription to relay {relay_url}: {e}")
    
    def _setup_event_handlers(self) -> None:
        """Set up event handlers."""
        # Register event handlers with the event manager
        self.event_manager.register_handler(1, self._handle_text_note_event)
        self.event_manager.register_handler(4, self._handle_encrypted_dm_event)
        self.event_manager.register_handler(1059, self._handle_gift_wrap_event)