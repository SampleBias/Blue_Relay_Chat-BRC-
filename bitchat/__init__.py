"""
Blue Relay Chat RPi 4 - Decentralized Messaging Client

A low-cost, decentralized, dual-transport messaging node for Raspberry Pi 4
that extends the Blue Relay Chat network into non-mobile environments.

Features:
- Bluetooth LE Mesh networking for local communication
- Nostr protocol integration for global communication
- End-to-end encryption for private messages
- Command-line interface for headless operation
- Resource-efficient design for RPi 4 hardware
"""

from .version import __version__, __version_info__

__all__ = ["__version__", "__version_info__"]