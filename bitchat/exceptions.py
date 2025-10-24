"""
Custom exception classes for bitchat RPi 4 client.

This module defines all custom exception classes used throughout the application
to provide clear error handling and debugging information.
"""


class BitchatError(Exception):
    """Base exception class for all bitchat errors."""
    pass


class ConfigurationError(BitchatError):
    """Raised when there's an error in application configuration."""
    pass


class DatabaseError(BitchatError):
    """Raised when there's an error in database operations."""
    pass


class NetworkError(BitchatError):
    """Base class for network-related errors."""
    pass


class BluetoothError(NetworkError):
    """Raised when there's an error in Bluetooth operations."""
    pass


class NostrError(NetworkError):
    """Raised when there's an error in Nostr protocol operations."""
    pass


class TransportError(NetworkError):
    """Raised when there's an error in transport layer operations."""
    pass


class CryptographyError(BitchatError):
    """Raised when there's an error in cryptographic operations."""
    pass


class IdentityError(BitchatError):
    """Raised when there's an error in identity management."""
    pass


class MessageError(BitchatError):
    """Raised when there's an error in message processing."""
    pass


class RoutingError(BitchatError):
    """Raised when there's an error in message routing."""
    pass


class QueueError(BitchatError):
    """Raised when there's an error in message queuing."""
    pass


class CLIError(BitchatError):
    """Raised when there's an error in CLI operations."""
    pass


class EmergencyWipeError(BitchatError):
    """Raised when there's an error during emergency wipe operations."""
    pass


class ProtocolError(BitchatError):
    """Raised when there's an error in protocol implementation."""
    pass


class ValidationError(BitchatError):
    """Raised when there's an error in data validation."""
    pass


class ResourceError(BitchatError):
    """Raised when there's insufficient system resources."""
    pass


class TimeoutError(BitchatError):
    """Raised when an operation times out."""
    pass