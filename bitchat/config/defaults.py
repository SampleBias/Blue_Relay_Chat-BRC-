"""
Default configuration values for bitchat RPi 4 client.

This module contains the default configuration settings that are used
when no configuration file is provided or when settings are missing.
"""

from typing import Dict, Any

DEFAULT_CONFIG: Dict[str, Dict[str, Any]] = {
    "application": {
        "name": "blue-relay-chat",
        "version": "0.1.0",
        "debug": False,
        "log_level": "INFO",
    },
    "storage": {
        "data_dir": "~/.local/share/blue-relay-chat",
        "database_file": "blue-relay-chat.db",
        "max_message_history": 10000,
        "auto_cleanup": True,
        "cleanup_interval_hours": 24,
    },
    "network": {
        "max_retries": 3,
        "retry_delay_seconds": 5,
        "connection_timeout_seconds": 30,
        "keepalive_interval_seconds": 60,
    },
    "bluetooth": {
        "adapter_name": "hci0",
        "scan_interval_seconds": 10,
        "advertisement_interval_seconds": 5,
        "max_peers": 50,
        "mesh_ttl": 7,
        "discovery_timeout_seconds": 30,
        "power_save_mode": True,
    },
    "nostr": {
        "relays": "wss://relay.damus.io,wss://nos.lol,wss://relay.snort.social",
        "max_relay_connections": 5,
        "subscription_limit": 10,
        "event_batch_size": 50,
        "connection_timeout_seconds": 15,
        "reconnect_interval_seconds": 30,
    },
    "security": {
        "encryption_algorithm": "ChaCha20-Poly1305",
        "key_derivation_iterations": 100000,
        "emergency_wipe_gpio": 18,
        "emergency_wipe_confirmations": 3,
    },
    "cli": {
        "refresh_rate_ms": 100,
        "max_display_lines": 1000,
        "timestamp_format": "%H:%M:%S",
        "show_system_messages": True,
        "auto_scroll": True,
    },
    "location": {
        "auto_detect_location": True,
        "geohash_precision": 5,
        "location_update_interval_minutes": 30,
    },
    "performance": {
        "max_cpu_usage_percent": 50,
        "max_memory_mb": 100,
        "message_queue_size": 1000,
        "compression_enabled": True,
        "compression_threshold_bytes": 100,
    },
    "channels": {
        "default_channel": "mesh #bluetooth",
        "auto_join_local_channels": True,
        "channel_history_limit": 500,
        "max_channel_name_length": 64,
    },
}