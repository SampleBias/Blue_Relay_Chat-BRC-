"""
Data models for bitchat RPi 4 client.

This module defines the data models used throughout the application
for messages, peers, channels, and other entities.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Any
from enum import Enum

from ..constants import TransportType, MessageType, ChannelType, PeerStatus, MessageStatus, QueueStatus


@dataclass
class Message:
    """Message data model."""
    
    id: str
    sender_id: str
    recipient_id: Optional[str] = None
    channel_id: Optional[str] = None
    content: str
    message_type: MessageType = MessageType.TEXT
    transport_type: Optional[TransportType] = None
    created_at: datetime = field(default_factory=datetime.now)
    received_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    status: MessageStatus = MessageStatus.PENDING
    encrypted: bool = False
    compressed: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert message to dictionary."""
        return {
            "id": self.id,
            "sender_id": self.sender_id,
            "recipient_id": self.recipient_id,
            "channel_id": self.channel_id,
            "content": self.content,
            "message_type": self.message_type.value,
            "transport_type": self.transport_type.value if self.transport_type else None,
            "created_at": self.created_at.isoformat(),
            "received_at": self.received_at.isoformat() if self.received_at else None,
            "delivered_at": self.delivered_at.isoformat() if self.delivered_at else None,
            "status": self.status.value,
            "encrypted": self.encrypted,
            "compressed": self.compressed,
            "metadata": self.metadata,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Message":
        """Create message from dictionary."""
        message = cls(
            id=data["id"],
            sender_id=data["sender_id"],
            recipient_id=data.get("recipient_id"),
            channel_id=data.get("channel_id"),
            content=data["content"],
            message_type=MessageType(data.get("message_type", MessageType.TEXT.value)),
            transport_type=TransportType(data["transport_type"]) if data.get("transport_type") else None,
            status=MessageStatus(data.get("status", MessageStatus.PENDING.value)),
            encrypted=data.get("encrypted", False),
            compressed=data.get("compressed", False),
            metadata=data.get("metadata", {}),
        )
        
        if "created_at" in data:
            message.created_at = datetime.fromisoformat(data["created_at"])
        if "received_at" in data and data["received_at"]:
            message.received_at = datetime.fromisoformat(data["received_at"])
        if "delivered_at" in data and data["delivered_at"]:
            message.delivered_at = datetime.fromisoformat(data["delivered_at"])
        
        return message


@dataclass
class Peer:
    """Peer data model."""
    
    id: str
    public_key: str
    last_seen: datetime = field(default_factory=datetime.now)
    transport_type: TransportType = TransportType.MESH
    is_local: bool = True
    status: PeerStatus = PeerStatus.OFFLINE
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert peer to dictionary."""
        return {
            "id": self.id,
            "public_key": self.public_key,
            "last_seen": self.last_seen.isoformat(),
            "transport_type": self.transport_type.value,
            "is_local": self.is_local,
            "status": self.status.value,
            "metadata": self.metadata,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Peer":
        """Create peer from dictionary."""
        peer = cls(
            id=data["id"],
            public_key=data["public_key"],
            transport_type=TransportType(data.get("transport_type", TransportType.MESH.value)),
            is_local=data.get("is_local", True),
            status=PeerStatus(data.get("status", PeerStatus.OFFLINE.value)),
            metadata=data.get("metadata", {}),
        )
        
        if "last_seen" in data:
            peer.last_seen = datetime.fromisoformat(data["last_seen"])
        
        return peer
    
    def is_online(self, timeout_minutes: int = 5) -> bool:
        """Check if peer is considered online."""
        return datetime.now() - self.last_seen < datetime.timedelta(minutes=timeout_minutes)


@dataclass
class Channel:
    """Channel data model."""
    
    id: str
    name: str
    channel_type: ChannelType = ChannelType.MESH
    is_private: bool = False
    created_at: datetime = field(default_factory=datetime.now)
    description: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert channel to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "channel_type": self.channel_type.value,
            "is_private": self.is_private,
            "created_at": self.created_at.isoformat(),
            "description": self.description,
            "metadata": self.metadata,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Channel":
        """Create channel from dictionary."""
        channel = cls(
            id=data["id"],
            name=data["name"],
            channel_type=ChannelType(data.get("channel_type", ChannelType.MESH.value)),
            is_private=data.get("is_private", False),
            description=data.get("description"),
            metadata=data.get("metadata", {}),
        )
        
        if "created_at" in data:
            channel.created_at = datetime.fromisoformat(data["created_at"])
        
        return channel


@dataclass
class QueuedMessage:
    """Queued message data model."""
    
    id: str
    message_id: str
    transport_type: TransportType
    retry_count: int = 0
    max_retries: int = 3
    next_retry: datetime = field(default_factory=datetime.now)
    status: QueueStatus = QueueStatus.ACTIVE
    priority: int = 0  # Higher number = higher priority
    created_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert queued message to dictionary."""
        return {
            "id": self.id,
            "message_id": self.message_id,
            "transport_type": self.transport_type.value,
            "retry_count": self.retry_count,
            "max_retries": self.max_retries,
            "next_retry": self.next_retry.isoformat(),
            "status": self.status.value,
            "priority": self.priority,
            "created_at": self.created_at.isoformat(),
            "metadata": self.metadata,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "QueuedMessage":
        """Create queued message from dictionary."""
        queued_message = cls(
            id=data["id"],
            message_id=data["message_id"],
            transport_type=TransportType(data["transport_type"]),
            retry_count=data.get("retry_count", 0),
            max_retries=data.get("max_retries", 3),
            status=QueueStatus(data.get("status", QueueStatus.ACTIVE.value)),
            priority=data.get("priority", 0),
            metadata=data.get("metadata", {}),
        )
        
        if "next_retry" in data:
            queued_message.next_retry = datetime.fromisoformat(data["next_retry"])
        if "created_at" in data:
            queued_message.created_at = datetime.fromisoformat(data["created_at"])
        
        return queued_message
    
    def should_retry(self) -> bool:
        """Check if message should be retried now."""
        return (
            self.status == QueueStatus.ACTIVE and
            self.retry_count < self.max_retries and
            datetime.now() >= self.next_retry
        )
    
    def increment_retry(self, delay_seconds: int = 5) -> None:
        """Increment retry count and schedule next retry."""
        self.retry_count += 1
        self.next_retry = datetime.now() + datetime.timedelta(seconds=delay_seconds * self.retry_count)
        
        if self.retry_count >= self.max_retries:
            self.status = QueueStatus.FAILED


@dataclass
class Identity:
    """Identity data model."""
    
    id: str
    public_key: str
    private_key: str  # Encrypted at rest
    key_algorithm: str = "ed25519"
    created_at: datetime = field(default_factory=datetime.now)
    last_used: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert identity to dictionary."""
        return {
            "id": self.id,
            "public_key": self.public_key,
            "private_key": self.private_key,  # Should be encrypted
            "key_algorithm": self.key_algorithm,
            "created_at": self.created_at.isoformat(),
            "last_used": self.last_used.isoformat() if self.last_used else None,
            "metadata": self.metadata,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Identity":
        """Create identity from dictionary."""
        identity = cls(
            id=data["id"],
            public_key=data["public_key"],
            private_key=data["private_key"],
            key_algorithm=data.get("key_algorithm", "ed25519"),
            metadata=data.get("metadata", {}),
        )
        
        if "created_at" in data:
            identity.created_at = datetime.fromisoformat(data["created_at"])
        if "last_used" in data and data["last_used"]:
            identity.last_used = datetime.fromisoformat(data["last_used"])
        
        return identity


@dataclass
class ConfigSetting:
    """Configuration setting data model."""
    
    key: str
    value: Any
    section: str
    description: Optional[str] = None
    data_type: str = "string"
    is_encrypted: bool = False
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert config setting to dictionary."""
        return {
            "key": self.key,
            "value": self.value,
            "section": self.section,
            "description": self.description,
            "data_type": self.data_type,
            "is_encrypted": self.is_encrypted,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ConfigSetting":
        """Create config setting from dictionary."""
        setting = cls(
            key=data["key"],
            value=data["value"],
            section=data["section"],
            description=data.get("description"),
            data_type=data.get("data_type", "string"),
            is_encrypted=data.get("is_encrypted", False),
        )
        
        if "created_at" in data:
            setting.created_at = datetime.fromisoformat(data["created_at"])
        if "updated_at" in data:
            setting.updated_at = datetime.fromisoformat(data["updated_at"])
        
        return setting