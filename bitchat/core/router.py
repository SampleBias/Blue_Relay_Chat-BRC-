"""
Message router for bitchat RPi 4 client.

This module contains the message routing logic that handles
intelligent routing between Bluetooth LE Mesh and Nostr transports.
"""

import asyncio
from typing import Dict, List, Optional, Set, Any
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum

from ..config.manager import ConfigManager
from ..utils.logging import get_logger
from ..exceptions import RoutingError, MessageError
from ..constants import TransportType, MessageType, MessageStatus
from .events import EventBus, Event, EventTypes


@dataclass
class Message:
    """Represents a message in the system."""
    
    id: str
    content: str
    sender_id: str
    recipient_id: Optional[str] = None
    channel_id: Optional[str] = None
    message_type: MessageType = MessageType.TEXT
    transport_type: Optional[TransportType] = None
    created_at: datetime = None
    status: MessageStatus = MessageStatus.PENDING
    retry_count: int = 0
    max_retries: int = 3
    encrypted: bool = False
    compressed: bool = False
    metadata: Dict[str, Any] = None
    
    def __post_init__(self) -> None:
        """Post-initialization processing."""
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.metadata is None:
            self.metadata = {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert message to dictionary representation."""
        return {
            "id": self.id,
            "content": self.content,
            "sender_id": self.sender_id,
            "recipient_id": self.recipient_id,
            "channel_id": self.channel_id,
            "message_type": self.message_type.value,
            "transport_type": self.transport_type.value if self.transport_type else None,
            "created_at": self.created_at.isoformat(),
            "status": self.status.value,
            "retry_count": self.retry_count,
            "max_retries": self.max_retries,
            "encrypted": self.encrypted,
            "compressed": self.compressed,
            "metadata": self.metadata,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Message":
        """Create message from dictionary representation."""
        message = cls(
            id=data["id"],
            content=data["content"],
            sender_id=data["sender_id"],
            recipient_id=data.get("recipient_id"),
            channel_id=data.get("channel_id"),
            message_type=MessageType(data.get("message_type", MessageType.TEXT.value)),
            transport_type=TransportType(data["transport_type"]) if data.get("transport_type") else None,
            status=MessageStatus(data.get("status", MessageStatus.PENDING.value)),
            retry_count=data.get("retry_count", 0),
            max_retries=data.get("max_retries", 3),
            encrypted=data.get("encrypted", False),
            compressed=data.get("compressed", False),
            metadata=data.get("metadata", {}),
        )
        
        if "created_at" in data:
            message.created_at = datetime.fromisoformat(data["created_at"])
        
        return message


@dataclass
class PeerInfo:
    """Information about a peer."""
    
    id: str
    transport_type: TransportType
    last_seen: datetime
    is_local: bool = True
    metadata: Dict[str, Any] = None
    
    def __post_init__(self) -> None:
        """Post-initialization processing."""
        if self.metadata is None:
            self.metadata = {}
    
    def is_online(self, timeout_minutes: int = 5) -> bool:
        """Check if peer is considered online."""
        return datetime.now() - self.last_seen < timedelta(minutes=timeout_minutes)


class MessageRouter:
    """Handles intelligent message routing between transports."""
    
    def __init__(self, config_manager: ConfigManager, event_bus: EventBus) -> None:
        """
        Initialize the message router.
        
        Args:
            config_manager: Configuration manager instance
            event_bus: Event bus for component communication
        """
        self.config = config_manager
        self.logger = get_logger("message_router")
        self.event_bus = event_bus
        
        # Router state
        self._running = False
        self._local_peers: Dict[str, PeerInfo] = {}
        self._message_queue: asyncio.Queue = asyncio.Queue()
        self._processing_task: Optional[asyncio.Task] = None
        
        # Routing configuration
        self._mesh_ttl = config_manager.get("bluetooth.mesh_ttl", 7)
        self._max_retries = config_manager.get("network.max_retries", 3)
        self._retry_delay = config_manager.get("network.retry_delay_seconds", 5)
        
        # Subscribe to events
        self._setup_event_subscriptions()
    
    def _setup_event_subscriptions(self) -> None:
        """Set up event subscriptions."""
        self.event_bus.subscribe(EventTypes.PEER_DISCOVERED, self._on_peer_discovered)
        self.event_bus.subscribe(EventTypes.PEER_LOST, self._on_peer_lost)
        self.event_bus.subscribe(EventTypes.MESSAGE_RECEIVED, self._on_message_received)
        self.event_bus.subscribe(EventTypes.TRANSPORT_CONNECTED, self._on_transport_connected)
        self.event_bus.subscribe(EventTypes.TRANSPORT_DISCONNECTED, self._on_transport_disconnected)
    
    async def start(self) -> None:
        """Start the message router."""
        if self._running:
            self.logger.warning("Message router is already running")
            return
        
        self._running = True
        self._processing_task = asyncio.create_task(self._process_messages())
        
        await self.event_bus.publish_sync(
            EventTypes.SYSTEM_STARTED,
            {"component": "message_router"},
            "message_router"
        )
        
        self.logger.info("Message router started")
    
    async def stop(self) -> None:
        """Stop the message router."""
        if not self._running:
            self.logger.debug("Message router is not running")
            return
        
        self._running = False
        
        if self._processing_task:
            self._processing_task.cancel()
            try:
                await self._processing_task
            except asyncio.CancelledError:
                pass
        
        # Clear queues
        while not self._message_queue.empty():
            try:
                self._message_queue.get_nowait()
            except asyncio.QueueEmpty:
                break
        
        await self.event_bus.publish_sync(
            EventTypes.SYSTEM_STOPPED,
            {"component": "message_router"},
            "message_router"
        )
        
        self.logger.info("Message router stopped")
    
    async def send_message(self, message: Message) -> bool:
        """
        Send a message through the appropriate transport.
        
        Args:
            message: Message to send
            
        Returns:
            True if message was queued successfully, False otherwise
        """
        try:
            # Determine the best transport for this message
            transport_type = await self._determine_transport(message)
            
            if transport_type:
                message.transport_type = transport_type
                message.status = MessageStatus.QUEUED
                
                await self._message_queue.put(message)
                
                await self.event_bus.publish(
                    create_message_event(EventTypes.MESSAGE_QUEUED, message.id, {
                        "transport_type": transport_type.value,
                    })
                )
                
                self.logger.debug(f"Queued message {message.id} for {transport_type.value} transport")
                return True
            else:
                message.status = MessageStatus.FAILED
                await self.event_bus.publish(
                    create_message_event(EventTypes.MESSAGE_FAILED, message.id, {
                        "reason": "No suitable transport available",
                    })
                )
                return False
                
        except Exception as e:
            self.logger.error(f"Error sending message {message.id}: {e}")
            message.status = MessageStatus.FAILED
            return False
    
    async def _determine_transport(self, message: Message) -> Optional[TransportType]:
        """
        Determine the best transport for a message.
        
        Args:
            message: Message to analyze
            
        Returns:
            Best transport type or None if no suitable transport
        """
        # If message is for a channel, check if it's a local channel
        if message.channel_id:
            if message.channel_id.startswith("mesh #"):
                return TransportType.MESH
            elif message.channel_id.startswith("block #"):
                return TransportType.NOSTR
        
        # If message has a specific recipient, check if they're local
        if message.recipient_id:
            if message.recipient_id in self._local_peers:
                peer = self._local_peers[message.recipient_id]
                if peer.is_online():
                    return TransportType.MESH
            
            # If recipient is not local or offline, use Nostr
            return TransportType.NOSTR
        
        # Default to mesh for local messages
        return TransportType.MESH
    
    async def _process_messages(self) -> None:
        """Process messages from the queue."""
        self.logger.debug("Starting message processor")
        
        while self._running:
            try:
                # Wait for a message with timeout
                message = await asyncio.wait_for(self._message_queue.get(), timeout=1.0)
                await self._handle_message(message)
            except asyncio.TimeoutError:
                continue
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error processing message: {e}")
        
        self.logger.debug("Message processor stopped")
    
    async def _handle_message(self, message: Message) -> None:
        """
        Handle a single message.
        
        Args:
            message: Message to handle
        """
        try:
            # Send the message through the appropriate transport
            success = await self._send_via_transport(message)
            
            if success:
                message.status = MessageStatus.SENT
                await self.event_bus.publish(
                    create_message_event(EventTypes.MESSAGE_SENT, message.id)
                )
                self.logger.debug(f"Sent message {message.id} via {message.transport_type.value}")
            else:
                await self._handle_send_failure(message)
                
        except Exception as e:
            self.logger.error(f"Error handling message {message.id}: {e}")
            await self._handle_send_failure(message)
    
    async def _send_via_transport(self, message: Message) -> bool:
        """
        Send a message via the specified transport.
        
        Args:
            message: Message to send
            
        Returns:
            True if sent successfully, False otherwise
        """
        # This will be implemented when transport modules are created
        # For now, just simulate the send
        if message.transport_type == TransportType.MESH:
            # await self.bluetooth_transport.send(message)
            await asyncio.sleep(0.1)  # Simulate network delay
            return True
        elif message.transport_type == TransportType.NOSTR:
            # await self.nostr_transport.send(message)
            await asyncio.sleep(0.2)  # Simulate network delay
            return True
        else:
            return False
    
    async def _handle_send_failure(self, message: Message) -> None:
        """
        Handle a message send failure.
        
        Args:
            message: Message that failed to send
        """
        message.retry_count += 1
        
        if message.retry_count < message.max_retries:
            # Retry after delay
            await asyncio.sleep(self._retry_delay * message.retry_count)
            await self._message_queue.put(message)
            
            self.logger.debug(f"Retrying message {message.id} (attempt {message.retry_count})")
        else:
            # Max retries reached, mark as failed
            message.status = MessageStatus.FAILED
            
            await self.event_bus.publish(
                create_message_event(EventTypes.MESSAGE_FAILED, message.id, {
                    "reason": "Max retries exceeded",
                    "retry_count": message.retry_count,
                })
            )
            
            self.logger.error(f"Message {message.id} failed after {message.retry_count} retries")
    
    async def _on_peer_discovered(self, event: Event) -> None:
        """Handle peer discovered event."""
        peer_id = event.data.get("peer_id")
        transport_type = TransportType(event.data.get("transport_type", "mesh"))
        
        if peer_id:
            peer = PeerInfo(
                id=peer_id,
                transport_type=transport_type,
                last_seen=datetime.now(),
                is_local=(transport_type == TransportType.MESH),
                metadata=event.data.get("metadata", {})
            )
            
            self._local_peers[peer_id] = peer
            self.logger.debug(f"Discovered peer {peer_id} via {transport_type.value}")
    
    async def _on_peer_lost(self, event: Event) -> None:
        """Handle peer lost event."""
        peer_id = event.data.get("peer_id")
        
        if peer_id and peer_id in self._local_peers:
            del self._local_peers[peer_id]
            self.logger.debug(f"Lost peer {peer_id}")
    
    async def _on_message_received(self, event: Event) -> None:
        """Handle message received event."""
        message_data = event.data.get("message")
        if message_data:
            message = Message.from_dict(message_data)
            
            # Process received message
            await self._process_received_message(message)
    
    async def _process_received_message(self, message: Message) -> None:
        """
        Process a received message.
        
        Args:
            message: Received message
        """
        # This will handle message decryption, decompression, etc.
        # For now, just log the message
        self.logger.info(f"Received message {message.id} from {message.sender_id}")
        
        # Publish message received event for other components
        await self.event_bus.publish(
            create_message_event(EventTypes.MESSAGE_RECEIVED, message.id, {
                "message": message.to_dict(),
            })
        )
    
    async def _on_transport_connected(self, event: Event) -> None:
        """Handle transport connected event."""
        transport_type = event.data.get("transport_type")
        self.logger.info(f"Transport {transport_type} connected")
    
    async def _on_transport_disconnected(self, event: Event) -> None:
        """Handle transport disconnected event."""
        transport_type = event.data.get("transport_type")
        self.logger.warning(f"Transport {transport_type} disconnected")
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get the current router status.
        
        Returns:
            Dictionary containing router status information
        """
        return {
            "running": self._running,
            "queue_size": self._message_queue.qsize(),
            "local_peers": len(self._local_peers),
            "online_peers": len([p for p in self._local_peers.values() if p.is_online()]),
            "peer_details": {
                peer_id: {
                    "transport_type": peer.transport_type.value,
                    "last_seen": peer.last_seen.isoformat(),
                    "is_online": peer.is_online(),
                    "is_local": peer.is_local,
                }
                for peer_id, peer in self._local_peers.items()
            }
        }


# Import the create_message_event function
def create_message_event(event_type: str, message_id: str, data: Dict[str, Any] = None) -> Event:
    """Create a message event."""
    event_data = data or {}
    event_data["message_id"] = message_id
    return Event(type=event_type, data=event_data, source="message_router")