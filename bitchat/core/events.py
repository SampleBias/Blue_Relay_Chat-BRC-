"""
Event system for bitchat RPi 4 client.

This module provides an event bus and event handling system for
communication between different components of the application.
"""

import asyncio
from typing import Any, Callable, Dict, List, Optional, Set
from dataclasses import dataclass, field
from datetime import datetime
import uuid

from ..utils.logging import get_logger
from ..exceptions import BitchatError


@dataclass
class Event:
    """Represents an event in the system."""
    
    type: str
    data: Dict[str, Any] = field(default_factory=dict)
    source: str = ""
    timestamp: datetime = field(default_factory=datetime.now)
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    
    def __post_init__(self) -> None:
        """Post-initialization processing."""
        if not self.type:
            raise ValueError("Event type cannot be empty")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary representation."""
        return {
            "type": self.type,
            "data": self.data,
            "source": self.source,
            "timestamp": self.timestamp.isoformat(),
            "event_id": self.event_id,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Event":
        """Create event from dictionary representation."""
        event = cls(
            type=data["type"],
            data=data.get("data", {}),
            source=data.get("source", ""),
            event_id=data.get("event_id", str(uuid.uuid4())),
        )
        
        if "timestamp" in data:
            event.timestamp = datetime.fromisoformat(data["timestamp"])
        
        return event


class EventBus:
    """Central event bus for component communication."""
    
    def __init__(self) -> None:
        """Initialize the event bus."""
        self.logger = get_logger("event_bus")
        self._subscribers: Dict[str, List[Callable]] = {}
        self._running = False
        self._event_queue: asyncio.Queue = asyncio.Queue()
        self._processor_task: Optional[asyncio.Task] = None
        self._lock = asyncio.Lock()
    
    async def start(self) -> None:
        """Start the event bus."""
        if self._running:
            self.logger.warning("Event bus is already running")
            return
        
        self._running = True
        self._processor_task = asyncio.create_task(self._process_events())
        self.logger.info("Event bus started")
    
    async def stop(self) -> None:
        """Stop the event bus."""
        if not self._running:
            self.logger.debug("Event bus is not running")
            return
        
        self._running = False
        
        if self._processor_task:
            self._processor_task.cancel()
            try:
                await self._processor_task
            except asyncio.CancelledError:
                pass
        
        # Clear the queue
        while not self._event_queue.empty():
            try:
                self._event_queue.get_nowait()
            except asyncio.QueueEmpty:
                break
        
        self.logger.info("Event bus stopped")
    
    async def close(self) -> None:
        """Close the event bus and clean up resources."""
        await self.stop()
        self._subscribers.clear()
        self.logger.info("Event bus closed")
    
    def subscribe(self, event_type: str, callback: Callable[[Event], None]) -> str:
        """
        Subscribe to an event type.
        
        Args:
            event_type: Type of event to subscribe to
            callback: Callback function to handle the event
            
        Returns:
            Subscription ID
        """
        if not callable(callback):
            raise ValueError("Callback must be callable")
        
        subscription_id = str(uuid.uuid4())
        
        async def _subscribe():
            async with self._lock:
                if event_type not in self._subscribers:
                    self._subscribers[event_type] = []
                
                self._subscribers[event_type].append({
                    "id": subscription_id,
                    "callback": callback,
                })
        
        # Run in current thread if event bus is not running, otherwise schedule
        if self._running:
            asyncio.create_task(_subscribe())
        else:
            asyncio.run(_subscribe())
        
        self.logger.debug(f"Subscribed to {event_type} with ID {subscription_id}")
        return subscription_id
    
    def unsubscribe(self, event_type: str, subscription_id: str) -> bool:
        """
        Unsubscribe from an event type.
        
        Args:
            event_type: Type of event to unsubscribe from
            subscription_id: Subscription ID to remove
            
        Returns:
            True if unsubscribed successfully, False otherwise
        """
        async def _unsubscribe():
            async with self._lock:
                if event_type not in self._subscribers:
                    return False
                
                for i, subscriber in enumerate(self._subscribers[event_type]):
                    if subscriber["id"] == subscription_id:
                        self._subscribers[event_type].pop(i)
                        self.logger.debug(f"Unsubscribed from {event_type} with ID {subscription_id}")
                        return True
                
                return False
        
        if self._running:
            return asyncio.run(_unsubscribe())
        else:
            return asyncio.run(_unsubscribe())
    
    async def publish(self, event: Event) -> None:
        """
        Publish an event to the bus.
        
        Args:
            event: Event to publish
        """
        if not isinstance(event, Event):
            raise ValueError("Event must be an instance of Event")
        
        if not self._running:
            self.logger.warning("Event bus is not running, dropping event")
            return
        
        try:
            await self._event_queue.put(event)
            self.logger.debug(f"Published event {event.type} ({event.event_id})")
        except asyncio.QueueFull:
            self.logger.error("Event queue is full, dropping event")
    
    async def publish_sync(self, event_type: str, data: Dict[str, Any], source: str = "") -> None:
        """
        Publish an event synchronously (convenience method).
        
        Args:
            event_type: Type of event
            data: Event data
            source: Event source
        """
        event = Event(type=event_type, data=data, source=source)
        await self.publish(event)
    
    async def _process_events(self) -> None:
        """Process events from the queue."""
        self.logger.debug("Starting event processor")
        
        while self._running:
            try:
                # Wait for an event with timeout to allow checking _running
                event = await asyncio.wait_for(self._event_queue.get(), timeout=1.0)
                await self._handle_event(event)
            except asyncio.TimeoutError:
                continue
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error processing event: {e}")
        
        self.logger.debug("Event processor stopped")
    
    async def _handle_event(self, event: Event) -> None:
        """
        Handle a single event.
        
        Args:
            event: Event to handle
        """
        async with self._lock:
            subscribers = self._subscribers.get(event.type, [])
            
            # Create tasks for all subscribers
            tasks = []
            for subscriber in subscribers:
                callback = subscriber["callback"]
                task = asyncio.create_task(self._safe_callback(callback, event))
                tasks.append(task)
            
            # Wait for all callbacks to complete (with timeout)
            if tasks:
                try:
                    await asyncio.wait_for(
                        asyncio.gather(*tasks, return_exceptions=True),
                        timeout=5.0
                    )
                except asyncio.TimeoutError:
                    self.logger.warning(f"Timeout handling event {event.type}")
        
        self.logger.debug(f"Handled event {event.type} for {len(subscribers)} subscribers")
    
    async def _safe_callback(self, callback: Callable[[Event], None], event: Event) -> None:
        """
        Safely execute a callback function.
        
        Args:
            callback: Callback function to execute
            event: Event to pass to callback
        """
        try:
            if asyncio.iscoroutinefunction(callback):
                await callback(event)
            else:
                callback(event)
        except Exception as e:
            self.logger.error(f"Error in event callback for {event.type}: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get event bus statistics.
        
        Returns:
            Dictionary containing statistics
        """
        return {
            "running": self._running,
            "queue_size": self._event_queue.qsize(),
            "subscribers": {
                event_type: len(subscribers)
                for event_type, subscribers in self._subscribers.items()
            },
            "total_subscriptions": sum(
                len(subscribers) for subscribers in self._subscribers.values()
            ),
        }


# Event type constants
class EventTypes:
    """Constants for event types used throughout the application."""
    
    # System events
    SYSTEM_STARTED = "system.started"
    SYSTEM_STOPPED = "system.stopped"
    SYSTEM_ERROR = "system.error"
    SYSTEM_SHUTDOWN = "system.shutdown"
    
    # Configuration events
    CONFIG_CHANGED = "config.changed"
    CONFIG_RELOADED = "config.reloaded"
    
    # Transport events
    TRANSPORT_CONNECTED = "transport.connected"
    TRANSPORT_DISCONNECTED = "transport.disconnected"
    TRANSPORT_ERROR = "transport.error"
    
    # Message events
    MESSAGE_RECEIVED = "message.received"
    MESSAGE_SENT = "message.sent"
    MESSAGE_DELIVERED = "message.delivered"
    MESSAGE_FAILED = "message.failed"
    MESSAGE_QUEUED = "message.queued"
    
    # Peer events
    PEER_CONNECTED = "peer.connected"
    PEER_DISCONNECTED = "peer.disconnected"
    PEER_DISCOVERED = "peer.discovered"
    PEER_LOST = "peer.lost"
    
    # Channel events
    CHANNEL_JOINED = "channel.joined"
    CHANNEL_LEFT = "channel.left"
    CHANNEL_MESSAGE = "channel.message"
    
    # Security events
    SECURITY_ERROR = "security.error"
    EMERGENCY_WIPE = "security.emergency_wipe"
    
    # CLI events
    CLI_COMMAND = "cli.command"
    CLI_OUTPUT = "cli.output"
    CLI_ERROR = "cli.error"


# Convenience functions for creating common events
def create_system_event(event_type: str, data: Dict[str, Any] = None) -> Event:
    """Create a system event."""
    return Event(type=event_type, data=data or {}, source="system")


def create_message_event(event_type: str, message_id: str, data: Dict[str, Any] = None) -> Event:
    """Create a message event."""
    event_data = data or {}
    event_data["message_id"] = message_id
    return Event(type=event_type, data=event_data, source="message_router")


def create_transport_event(event_type: str, transport_type: str, data: Dict[str, Any] = None) -> Event:
    """Create a transport event."""
    event_data = data or {}
    event_data["transport_type"] = transport_type
    return Event(type=event_type, data=event_data, source="transport")


def create_peer_event(event_type: str, peer_id: str, data: Dict[str, Any] = None) -> Event:
    """Create a peer event."""
    event_data = data or {}
    event_data["peer_id"] = peer_id
    return Event(type=event_type, data=event_data, source="peer_manager")