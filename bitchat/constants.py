"""
Application constants for bitchat RPi 4 client.

This module defines all constant values used throughout the application
to ensure consistency and maintainability.
"""

from enum import Enum
from typing import Final

# Application constants
APP_NAME: Final[str] = "blue-relay-chat"
DEFAULT_CONFIG_FILE: Final[str] = "config.ini"
DEFAULT_DATA_DIR: Final[str] = "~/.local/share/blue-relay-chat"
DEFAULT_DATABASE_FILE: Final[str] = "blue-relay-chat.db"

# Network constants
DEFAULT_MESH_TTL: Final[int] = 7
DEFAULT_MAX_PEERS: Final[int] = 50
DEFAULT_MAX_RETRIES: Final[int] = 3
DEFAULT_RETRY_DELAY: Final[int] = 5
DEFAULT_CONNECTION_TIMEOUT: Final[int] = 30
DEFAULT_KEEPALIVE_INTERVAL: Final[int] = 60

# Bluetooth constants
DEFAULT_SCAN_INTERVAL: Final[int] = 10
DEFAULT_ADVERTISEMENT_INTERVAL: Final[int] = 5
DEFAULT_DISCOVERY_TIMEOUT: Final[int] = 30
DEFAULT_ADAPTER_NAME: Final[str] = "hci0"

# Nostr constants
DEFAULT_MAX_RELAY_CONNECTIONS: Final[int] = 5
DEFAULT_SUBSCRIPTION_LIMIT: Final[int] = 10
DEFAULT_EVENT_BATCH_SIZE: Final[int] = 50
DEFAULT_RECONNECT_INTERVAL: Final[int] = 30

# Security constants
DEFAULT_KEY_DERIVATION_ITERATIONS: Final[int] = 100000
DEFAULT_EMERGENCY_WIPE_CONFIRMATIONS: Final[int] = 3
DEFAULT_EMERGENCY_WIPE_GPIO: Final[int] = 18

# CLI constants
DEFAULT_REFRESH_RATE: Final[int] = 100
DEFAULT_MAX_DISPLAY_LINES: Final[int] = 1000
DEFAULT_TIMESTAMP_FORMAT: Final[str] = "%H:%M:%S"

# Performance constants
DEFAULT_MAX_CPU_USAGE: Final[int] = 50
DEFAULT_MAX_MEMORY_MB: Final[int] = 100
DEFAULT_MESSAGE_QUEUE_SIZE: Final[int] = 1000
DEFAULT_COMPRESSION_THRESHOLD: Final[int] = 100

# Channel constants
DEFAULT_CHANNEL: Final[str] = "mesh #bluetooth"
DEFAULT_CHANNEL_HISTORY_LIMIT: Final[int] = 500
DEFAULT_MAX_CHANNEL_NAME_LENGTH: Final[int] = 64

# Location constants
DEFAULT_GEOHASH_PRECISION: Final[int] = 5
DEFAULT_LOCATION_UPDATE_INTERVAL: Final[int] = 30  # minutes

# Database constants
DEFAULT_MAX_MESSAGE_HISTORY: Final[int] = 10000
DEFAULT_CLEANUP_INTERVAL_HOURS: Final[int] = 24

# Message constants
MAX_MESSAGE_SIZE: Final[int] = 65536  # 64KB
MAX_MESSAGE_AGE_DAYS: Final[int] = 30

# Protocol constants
PROTOCOL_VERSION: Final[str] = "1.0"
MAGIC_BYTES: Final[bytes] = b"BRC1"  # Bitchat Relay Chat v1


class TransportType(Enum):
    """Enumeration of supported transport types."""
    MESH = "mesh"
    NOSTR = "nostr"


class MessageType(Enum):
    """Enumeration of message types."""
    TEXT = "text"
    SYSTEM = "system"
    PRIVATE = "private"
    CHANNEL = "channel"
    CONTROL = "control"


class ChannelType(Enum):
    """Enumeration of channel types."""
    MESH = "mesh"
    LOCATION = "location"
    PRIVATE = "private"
    SYSTEM = "system"


class LogLevel(Enum):
    """Enumeration of log levels."""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class PeerStatus(Enum):
    """Enumeration of peer status values."""
    ONLINE = "online"
    OFFLINE = "offline"
    CONNECTING = "connecting"
    ERROR = "error"


class MessageStatus(Enum):
    """Enumeration of message status values."""
    PENDING = "pending"
    SENT = "sent"
    DELIVERED = "delivered"
    FAILED = "failed"
    QUEUED = "queued"


class QueueStatus(Enum):
    """Enumeration of queue status values."""
    ACTIVE = "active"
    RETRYING = "retrying"
    FAILED = "failed"
    COMPLETED = "completed"


# Command constants
COMMAND_PREFIX: Final[str] = "/"
AVAILABLE_COMMANDS: Final[list] = [
    "help",
    "join",
    "leave",
    "msg",
    "who",
    "status",
    "config",
    "wipe",
    "list",
    "create",
    "invite",
    "slap",
]

# System message prefixes
SYSTEM_MESSAGE_PREFIX: Final[str] = "System:"
ERROR_MESSAGE_PREFIX: Final[str] = "Error:"

# Encryption constants
ENCRYPTION_ALGORITHM: Final[str] = "ChaCha20-Poly1305"
KEY_SIZE: Final[int] = 32  # 256 bits
NONCE_SIZE: Final[int] = 12  # 96 bits
TAG_SIZE: Final[int] = 16  # 128 bits

# Compression constants
COMPRESSION_ALGORITHM: Final[str] = "lz4"

# GPIO constants for emergency wipe
GPIO_MODE: Final[str] = "BCM"
GPIO_PULL_UP_DOWN: Final[str] = "PUD_UP"
GPIO_EDGE: Final[str] = "FALLING"

# WebSocket constants
WEBSOCKET_PING_INTERVAL: Final[int] = 20
WEBSOCKET_PING_TIMEOUT: Final[int] = 20
WEBSOCKET_CLOSE_TIMEOUT: Final[int] = 10

# Rate limiting constants
RATE_LIMIT_MESSAGES_PER_MINUTE: Final[int] = 60
RATE_LIMIT_BURST_SIZE: Final[int] = 10

# File size constants
MAX_CONFIG_FILE_SIZE: Final[int] = 1024 * 1024  # 1MB
MAX_LOG_FILE_SIZE: Final[int] = 10 * 1024 * 1024  # 10MB
MAX_DATABASE_SIZE: Final[int] = 100 * 1024 * 1024  # 100MB