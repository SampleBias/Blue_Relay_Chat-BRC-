"""
Message queue implementation for Blue Relay Chat RPi 4 client.

This module provides a persistent message queue for handling
outgoing messages with retry logic and priority handling.
"""

import asyncio
import uuid
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from dataclasses import asdict

from ..config.manager import ConfigManager
from ..utils.logging import get_logger
from ..exceptions import QueueError
from ..constants import TransportType, QueueStatus
from ..data.models import QueuedMessage
from .database import DatabaseManager


class MessageQueue:
    """Manages queued messages with persistence and retry logic."""
    
    def __init__(self, config_manager: ConfigManager, database: DatabaseManager) -> None:
        """
        Initialize the message queue.
        
        Args:
            config_manager: Configuration manager instance
            database: Database manager instance
        """
        self.config = config_manager
        self.db = database
        self.logger = get_logger("message_queue")
        
        # Queue configuration
        self.max_queue_size = config_manager.get("performance.message_queue_size", 1000)
        self.max_retries = config_manager.get("network.max_retries", 3)
        self.retry_delay = config_manager.get("network.retry_delay_seconds", 5)
        self.retry_backoff_multiplier = 2.0
        
        # In-memory cache for active messages
        self._queue_cache: Dict[str, QueuedMessage] = {}
        self._processing = False
        self._processor_task: Optional[asyncio.Task] = None
    
    async def initialize(self) -> None:
        """Initialize the message queue."""
        try:
            # Load pending messages from database
            await self._load_pending_messages()
            
            # Start the message processor
            await self.start_processing()
            
            self.logger.info("Message queue initialized")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize message queue: {e}")
            raise QueueError(f"Message queue initialization failed: {e}")
    
    async def _load_pending_messages(self) -> None:
        """Load pending messages from the database."""
        try:
            pending_messages = await self.db.get_pending_queued_messages(limit=self.max_queue_size)
            
            for msg_data in pending_messages:
                queued_message = QueuedMessage.from_dict(msg_data)
                self._queue_cache[queued_message.id] = queued_message
            
            self.logger.info(f"Loaded {len(pending_messages)} pending messages")
            
        except Exception as e:
            self.logger.error(f"Failed to load pending messages: {e}")
            raise QueueError(f"Failed to load pending messages: {e}")
    
    async def enqueue(
        self,
        message_id: str,
        transport_type: TransportType,
        priority: int = 0,
        max_retries: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Add a message to the queue.
        
        Args:
            message_id: ID of the message to queue
            transport_type: Transport type for the message
            priority: Message priority (higher = more important)
            max_retries: Maximum retry attempts
            metadata: Additional metadata
            
        Returns:
            Queue entry ID
        """
        try:
            # Check queue size limit
            if len(self._queue_cache) >= self.max_queue_size:
                # Remove oldest low-priority messages
                await self._cleanup_old_messages()
            
            # Create queued message
            queued_message = QueuedMessage(
                id=str(uuid.uuid4()),
                message_id=message_id,
                transport_type=transport_type,
                max_retries=max_retries or self.max_retries,
                priority=priority,
                metadata=metadata or {}
            )
            
            # Save to database
            await self.db.save_queued_message(queued_message)
            
            # Add to cache
            self._queue_cache[queued_message.id] = queued_message
            
            self.logger.debug(f"Enqueued message {message_id} for {transport_type.value}")
            return queued_message.id
            
        except Exception as e:
            self.logger.error(f"Failed to enqueue message {message_id}: {e}")
            raise QueueError(f"Failed to enqueue message: {e}")
    
    async def dequeue(self, limit: int = 10) -> List[QueuedMessage]:
        """
        Get messages ready for processing.
        
        Args:
            limit: Maximum number of messages to return
            
        Returns:
            List of queued messages ready for processing
        """
        try:
            now = datetime.now()
            ready_messages = []
            
            # Find messages ready for processing
            for queued_message in self._queue_cache.values():
                if queued_message.should_retry() and queued_message.status == QueueStatus.ACTIVE:
                    ready_messages.append(queued_message)
            
            # Sort by priority (highest first) and then by creation time (oldest first)
            ready_messages.sort(key=lambda m: (-m.priority, m.created_at))
            
            # Limit results
            result = ready_messages[:limit]
            
            # Mark as being processed
            for message in result:
                message.status = QueueStatus.RETRYING
                await self.db.save_queued_message(message)
            
            self.logger.debug(f"Dequeued {len(result)} messages for processing")
            return result
            
        except Exception as e:
            self.logger.error(f"Failed to dequeue messages: {e}")
            raise QueueError(f"Failed to dequeue messages: {e}")
    
    async def mark_success(self, queue_id: str) -> None:
        """
        Mark a queued message as successfully sent.
        
        Args:
            queue_id: Queue entry ID
        """
        try:
            if queue_id not in self._queue_cache:
                self.logger.warning(f"Queue entry {queue_id} not found")
                return
            
            queued_message = self._queue_cache[queue_id]
            queued_message.status = QueueStatus.COMPLETED
            
            # Save to database
            await self.db.save_queued_message(queued_message)
            
            # Remove from cache after a delay
            await asyncio.sleep(60)  # Keep for 1 minute for status checks
            self._queue_cache.pop(queue_id, None)
            
            self.logger.debug(f"Marked queue entry {queue_id} as successful")
            
        except Exception as e:
            self.logger.error(f"Failed to mark queue entry {queue_id} as successful: {e}")
            raise QueueError(f"Failed to mark message as successful: {e}")
    
    async def mark_failed(self, queue_id: str, error: Optional[str] = None) -> None:
        """
        Mark a queued message as failed and schedule retry if appropriate.
        
        Args:
            queue_id: Queue entry ID
            error: Optional error message
        """
        try:
            if queue_id not in self._queue_cache:
                self.logger.warning(f"Queue entry {queue_id} not found")
                return
            
            queued_message = self._queue_cache[queue_id]
            
            # Increment retry count and schedule next retry
            queued_message.increment_retry(self.retry_delay)
            
            # Add error to metadata
            if error:
                if "errors" not in queued_message.metadata:
                    queued_message.metadata["errors"] = []
                queued_message.metadata["errors"].append({
                    "error": error,
                    "timestamp": datetime.now().isoformat(),
                    "retry_count": queued_message.retry_count,
                })
            
            # Save to database
            await self.db.save_queued_message(queued_message)
            
            if queued_message.status == QueueStatus.FAILED:
                # Remove from cache if max retries exceeded
                self._queue_cache.pop(queue_id, None)
                self.logger.error(f"Queue entry {queue_id} failed permanently after {queued_message.retry_count} retries")
            else:
                self.logger.debug(f"Queue entry {queue_id} scheduled for retry {queued_message.retry_count}/{queued_message.max_retries}")
            
        except Exception as e:
            self.logger.error(f"Failed to mark queue entry {queue_id} as failed: {e}")
            raise QueueError(f"Failed to mark message as failed: {e}")
    
    async def start_processing(self) -> None:
        """Start the message processing loop."""
        if self._processing:
            self.logger.warning("Message processing already started")
            return
        
        self._processing = True
        self._processor_task = asyncio.create_task(self._processing_loop())
        self.logger.info("Message processing started")
    
    async def stop_processing(self) -> None:
        """Stop the message processing loop."""
        if not self._processing:
            return
        
        self._processing = False
        
        if self._processor_task:
            self._processor_task.cancel()
            try:
                await self._processor_task
            except asyncio.CancelledError:
                pass
        
        self.logger.info("Message processing stopped")
    
    async def _processing_loop(self) -> None:
        """Main message processing loop."""
        self.logger.debug("Starting message processing loop")
        
        while self._processing:
            try:
                # Get messages ready for processing
                messages = await self.dequeue(limit=10)
                
                if messages:
                    # Process messages (this would be handled by the transport layer)
                    for message in messages:
                        # Publish event for transport layer to handle
                        from ..core.events import EventBus, EventTypes
                        # This would be injected or passed in a real implementation
                        # await self.event_bus.publish(Event(
                        #     type=EventTypes.QUEUE_MESSAGE_READY,
                        #     data={"queue_id": message.id, "message_id": message.message_id},
                        #     source="message_queue"
                        # ))
                        pass
                
                # Wait before next iteration
                await asyncio.sleep(1.0)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in message processing loop: {e}")
                await asyncio.sleep(5.0)  # Wait longer on error
        
        self.logger.debug("Message processing loop stopped")
    
    async def _cleanup_old_messages(self) -> None:
        """Remove old completed messages from the queue."""
        try:
            # Find completed messages older than 1 hour
            cutoff_time = datetime.now() - timedelta(hours=1)
            to_remove = []
            
            for queue_id, message in self._queue_cache.items():
                if (message.status == QueueStatus.COMPLETED and 
                    message.created_at < cutoff_time):
                    to_remove.append(queue_id)
            
            # Remove from cache
            for queue_id in to_remove:
                self._queue_cache.pop(queue_id, None)
            
            if to_remove:
                self.logger.debug(f"Cleaned up {len(to_remove)} old queue entries")
                
        except Exception as e:
            self.logger.error(f"Failed to cleanup old messages: {e}")
    
    async def get_queue_status(self) -> Dict[str, Any]:
        """
        Get the current status of the message queue.
        
        Returns:
            Dictionary containing queue status information
        """
        try:
            status_counts = {}
            transport_counts = {}
            
            for message in self._queue_cache.values():
                # Count by status
                status = message.status.value
                status_counts[status] = status_counts.get(status, 0) + 1
                
                # Count by transport type
                transport = message.transport_type.value
                transport_counts[transport] = transport_counts.get(transport, 0) + 1
            
            return {
                "total_messages": len(self._queue_cache),
                "max_queue_size": self.max_queue_size,
                "processing_active": self._processing,
                "status_counts": status_counts,
                "transport_counts": transport_counts,
                "ready_for_retry": len([m for m in self._queue_cache.values() if m.should_retry()]),
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get queue status: {e}")
            return {"error": str(e)}
    
    async def get_message_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get message history from the queue.
        
        Args:
            limit: Maximum number of messages to return
            
        Returns:
            List of message history entries
        """
        try:
            # Get all messages from cache, sorted by creation time
            messages = list(self._queue_cache.values())
            messages.sort(key=lambda m: m.created_at, reverse=True)
            
            # Convert to dictionaries and limit results
            history = []
            for message in messages[:limit]:
                history.append({
                    "id": message.id,
                    "message_id": message.message_id,
                    "transport_type": message.transport_type.value,
                    "status": message.status.value,
                    "retry_count": message.retry_count,
                    "max_retries": message.max_retries,
                    "priority": message.priority,
                    "created_at": message.created_at.isoformat(),
                    "next_retry": message.next_retry.isoformat(),
                })
            
            return history
            
        except Exception as e:
            self.logger.error(f"Failed to get message history: {e}")
            return []
    
    async def clear_queue(self, transport_type: Optional[TransportType] = None) -> int:
        """
        Clear messages from the queue.
        
        Args:
            transport_type: Optional transport type filter
            
        Returns:
            Number of messages cleared
        """
        try:
            to_remove = []
            
            for queue_id, message in self._queue_cache.items():
                if transport_type is None or message.transport_type == transport_type:
                    to_remove.append(queue_id)
            
            # Remove from cache and database
            for queue_id in to_remove:
                self._queue_cache.pop(queue_id, None)
                # Also remove from database
                await self.db.execute("DELETE FROM queued_messages WHERE id = ?", (queue_id,))
            
            self.logger.info(f"Cleared {len(to_remove)} messages from queue")
            return len(to_remove)
            
        except Exception as e:
            self.logger.error(f"Failed to clear queue: {e}")
            raise QueueError(f"Failed to clear queue: {e}")