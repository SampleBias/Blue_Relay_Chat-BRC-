"""
Configuration validation for bitchat RPi 4 client.

This module provides validation functions for configuration values
to ensure they meet the required constraints and formats.
"""

import os
import re
from typing import Any, Dict, List, Optional

from ..exceptions import ConfigurationError, ValidationError
from ..constants import (
    LogLevel,
    DEFAULT_MESH_TTL,
    DEFAULT_MAX_PEERS,
    DEFAULT_MAX_RETRIES,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_ADVERTISEMENT_INTERVAL,
    DEFAULT_DISCOVERY_TIMEOUT,
    DEFAULT_KEY_DERIVATION_ITERATIONS,
    DEFAULT_EMERGENCY_WIPE_CONFIRMATIONS,
    DEFAULT_EMERGENCY_WIPE_GPIO,
    DEFAULT_REFRESH_RATE,
    DEFAULT_MAX_DISPLAY_LINES,
    DEFAULT_GEOHASH_PRECISION,
    DEFAULT_LOCATION_UPDATE_INTERVAL,
    DEFAULT_MAX_CPU_USAGE,
    DEFAULT_MAX_MEMORY_MB,
    DEFAULT_MESSAGE_QUEUE_SIZE,
    DEFAULT_COMPRESSION_THRESHOLD,
    DEFAULT_CHANNEL_HISTORY_LIMIT,
    DEFAULT_MAX_CHANNEL_NAME_LENGTH,
)


class ConfigValidator:
    """Validates configuration values and ensures they meet requirements."""
    
    @staticmethod
    def validate_section(section: str, config: Dict[str, Any]) -> None:
        """Validate a configuration section."""
        if section == "application":
            ConfigValidator._validate_application(config)
        elif section == "storage":
            ConfigValidator._validate_storage(config)
        elif section == "network":
            ConfigValidator._validate_network(config)
        elif section == "bluetooth":
            ConfigValidator._validate_bluetooth(config)
        elif section == "nostr":
            ConfigValidator._validate_nostr(config)
        elif section == "security":
            ConfigValidator._validate_security(config)
        elif section == "cli":
            ConfigValidator._validate_cli(config)
        elif section == "location":
            ConfigValidator._validate_location(config)
        elif section == "performance":
            ConfigValidator._validate_performance(config)
        elif section == "channels":
            ConfigValidator._validate_channels(config)
        else:
            raise ConfigurationError(f"Unknown configuration section: {section}")
    
    @staticmethod
    def _validate_application(config: Dict[str, Any]) -> None:
        """Validate application configuration."""
        if "name" in config:
            if not isinstance(config["name"], str) or not config["name"].strip():
                raise ValidationError("Application name must be a non-empty string")
        
        if "version" in config:
            if not isinstance(config["version"], str) or not re.match(r"^\d+\.\d+\.\d+$", config["version"]):
                raise ValidationError("Version must be in format x.y.z")
        
        if "debug" in config:
            if not isinstance(config["debug"], bool):
                raise ValidationError("Debug must be a boolean value")
        
        if "log_level" in config:
            try:
                LogLevel(config["log_level"].upper())
            except ValueError:
                valid_levels = [level.value for level in LogLevel]
                raise ValidationError(f"Log level must be one of: {', '.join(valid_levels)}")
    
    @staticmethod
    def _validate_storage(config: Dict[str, Any]) -> None:
        """Validate storage configuration."""
        if "data_dir" in config:
            ConfigValidator._validate_path(config["data_dir"], "data_dir")
        
        if "database_file" in config:
            if not isinstance(config["database_file"], str) or not config["database_file"].strip():
                raise ValidationError("Database file must be a non-empty string")
        
        if "max_message_history" in config:
            ConfigValidator._validate_positive_integer(config["max_message_history"], "max_message_history")
        
        if "auto_cleanup" in config:
            if not isinstance(config["auto_cleanup"], bool):
                raise ValidationError("Auto cleanup must be a boolean value")
        
        if "cleanup_interval_hours" in config:
            ConfigValidator._validate_positive_integer(config["cleanup_interval_hours"], "cleanup_interval_hours")
    
    @staticmethod
    def _validate_network(config: Dict[str, Any]) -> None:
        """Validate network configuration."""
        if "max_retries" in config:
            ConfigValidator._validate_positive_integer(config["max_retries"], "max_retries")
        
        if "retry_delay_seconds" in config:
            ConfigValidator._validate_positive_integer(config["retry_delay_seconds"], "retry_delay_seconds")
        
        if "connection_timeout_seconds" in config:
            ConfigValidator._validate_positive_integer(config["connection_timeout_seconds"], "connection_timeout_seconds")
        
        if "keepalive_interval_seconds" in config:
            ConfigValidator._validate_positive_integer(config["keepalive_interval_seconds"], "keepalive_interval_seconds")
    
    @staticmethod
    def _validate_bluetooth(config: Dict[str, Any]) -> None:
        """Validate Bluetooth configuration."""
        if "adapter_name" in config:
            if not isinstance(config["adapter_name"], str) or not config["adapter_name"].strip():
                raise ValidationError("Adapter name must be a non-empty string")
        
        if "scan_interval_seconds" in config:
            ConfigValidator._validate_positive_integer(config["scan_interval_seconds"], "scan_interval_seconds")
        
        if "advertisement_interval_seconds" in config:
            ConfigValidator._validate_positive_integer(config["advertisement_interval_seconds"], "advertisement_interval_seconds")
        
        if "max_peers" in config:
            ConfigValidator._validate_positive_integer(config["max_peers"], "max_peers")
        
        if "mesh_ttl" in config:
            ConfigValidator._validate_range(config["mesh_ttl"], "mesh_ttl", 1, 127)
        
        if "discovery_timeout_seconds" in config:
            ConfigValidator._validate_positive_integer(config["discovery_timeout_seconds"], "discovery_timeout_seconds")
        
        if "power_save_mode" in config:
            if not isinstance(config["power_save_mode"], bool):
                raise ValidationError("Power save mode must be a boolean value")
    
    @staticmethod
    def _validate_nostr(config: Dict[str, Any]) -> None:
        """Validate Nostr configuration."""
        if "relays" in config:
            if isinstance(config["relays"], str):
                relays = config["relays"].split(",")
                for relay in relays:
                    if not ConfigValidator._is_valid_websocket_url(relay.strip()):
                        raise ValidationError(f"Invalid WebSocket URL: {relay}")
            elif isinstance(config["relays"], list):
                for relay in config["relays"]:
                    if not ConfigValidator._is_valid_websocket_url(relay):
                        raise ValidationError(f"Invalid WebSocket URL: {relay}")
            else:
                raise ValidationError("Relays must be a comma-separated string or list")
        
        if "max_relay_connections" in config:
            ConfigValidator._validate_positive_integer(config["max_relay_connections"], "max_relay_connections")
        
        if "subscription_limit" in config:
            ConfigValidator._validate_positive_integer(config["subscription_limit"], "subscription_limit")
        
        if "event_batch_size" in config:
            ConfigValidator._validate_positive_integer(config["event_batch_size"], "event_batch_size")
        
        if "connection_timeout_seconds" in config:
            ConfigValidator._validate_positive_integer(config["connection_timeout_seconds"], "connection_timeout_seconds")
        
        if "reconnect_interval_seconds" in config:
            ConfigValidator._validate_positive_integer(config["reconnect_interval_seconds"], "reconnect_interval_seconds")
    
    @staticmethod
    def _validate_security(config: Dict[str, Any]) -> None:
        """Validate security configuration."""
        if "encryption_algorithm" in config:
            valid_algorithms = ["ChaCha20-Poly1305", "AES-256-GCM"]
            if config["encryption_algorithm"] not in valid_algorithms:
                raise ValidationError(f"Encryption algorithm must be one of: {', '.join(valid_algorithms)}")
        
        if "key_derivation_iterations" in config:
            ConfigValidator._validate_positive_integer(config["key_derivation_iterations"], "key_derivation_iterations")
        
        if "emergency_wipe_gpio" in config:
            ConfigValidator._validate_gpio_pin(config["emergency_wipe_gpio"], "emergency_wipe_gpio")
        
        if "emergency_wipe_confirmations" in config:
            ConfigValidator._validate_range(config["emergency_wipe_confirmations"], "emergency_wipe_confirmations", 1, 10)
    
    @staticmethod
    def _validate_cli(config: Dict[str, Any]) -> None:
        """Validate CLI configuration."""
        if "refresh_rate_ms" in config:
            ConfigValidator._validate_positive_integer(config["refresh_rate_ms"], "refresh_rate_ms")
        
        if "max_display_lines" in config:
            ConfigValidator._validate_positive_integer(config["max_display_lines"], "max_display_lines")
        
        if "timestamp_format" in config:
            try:
                import time
                time.strftime(config["timestamp_format"])
            except ValueError:
                raise ValidationError("Invalid timestamp format")
        
        if "show_system_messages" in config:
            if not isinstance(config["show_system_messages"], bool):
                raise ValidationError("Show system messages must be a boolean value")
        
        if "auto_scroll" in config:
            if not isinstance(config["auto_scroll"], bool):
                raise ValidationError("Auto scroll must be a boolean value")
    
    @staticmethod
    def _validate_location(config: Dict[str, Any]) -> None:
        """Validate location configuration."""
        if "auto_detect_location" in config:
            if not isinstance(config["auto_detect_location"], bool):
                raise ValidationError("Auto detect location must be a boolean value")
        
        if "geohash_precision" in config:
            ConfigValidator._validate_range(config["geohash_precision"], "geohash_precision", 1, 12)
        
        if "location_update_interval_minutes" in config:
            ConfigValidator._validate_positive_integer(config["location_update_interval_minutes"], "location_update_interval_minutes")
    
    @staticmethod
    def _validate_performance(config: Dict[str, Any]) -> None:
        """Validate performance configuration."""
        if "max_cpu_usage_percent" in config:
            ConfigValidator._validate_range(config["max_cpu_usage_percent"], "max_cpu_usage_percent", 1, 100)
        
        if "max_memory_mb" in config:
            ConfigValidator._validate_positive_integer(config["max_memory_mb"], "max_memory_mb")
        
        if "message_queue_size" in config:
            ConfigValidator._validate_positive_integer(config["message_queue_size"], "message_queue_size")
        
        if "compression_enabled" in config:
            if not isinstance(config["compression_enabled"], bool):
                raise ValidationError("Compression enabled must be a boolean value")
        
        if "compression_threshold_bytes" in config:
            ConfigValidator._validate_positive_integer(config["compression_threshold_bytes"], "compression_threshold_bytes")
    
    @staticmethod
    def _validate_channels(config: Dict[str, Any]) -> None:
        """Validate channels configuration."""
        if "default_channel" in config:
            if not isinstance(config["default_channel"], str) or not config["default_channel"].strip():
                raise ValidationError("Default channel must be a non-empty string")
        
        if "auto_join_local_channels" in config:
            if not isinstance(config["auto_join_local_channels"], bool):
                raise ValidationError("Auto join local channels must be a boolean value")
        
        if "channel_history_limit" in config:
            ConfigValidator._validate_positive_integer(config["channel_history_limit"], "channel_history_limit")
        
        if "max_channel_name_length" in config:
            ConfigValidator._validate_positive_integer(config["max_channel_name_length"], "max_channel_name_length")
    
    @staticmethod
    def _validate_path(path: str, name: str) -> None:
        """Validate a file path."""
        if not isinstance(path, str) or not path.strip():
            raise ValidationError(f"{name} must be a non-empty string")
        
        # Expand user path if needed
        expanded_path = os.path.expanduser(path)
        
        # Check if the path is accessible
        try:
            parent_dir = os.path.dirname(expanded_path)
            if parent_dir and not os.path.exists(parent_dir):
                # Try to create the parent directory
                os.makedirs(parent_dir, exist_ok=True)
        except OSError as e:
            raise ValidationError(f"Cannot access or create directory for {name}: {e}")
    
    @staticmethod
    def _validate_positive_integer(value: Any, name: str) -> None:
        """Validate that a value is a positive integer."""
        if not isinstance(value, int) or value <= 0:
            raise ValidationError(f"{name} must be a positive integer")
    
    @staticmethod
    def _validate_range(value: Any, name: str, min_val: int, max_val: int) -> None:
        """Validate that a value is within a specified range."""
        if not isinstance(value, int) or not (min_val <= value <= max_val):
            raise ValidationError(f"{name} must be an integer between {min_val} and {max_val}")
    
    @staticmethod
    def _validate_gpio_pin(value: Any, name: str) -> None:
        """Validate a GPIO pin number."""
        if not isinstance(value, int):
            raise ValidationError(f"{name} must be an integer")
        
        # Valid GPIO pins for Raspberry Pi (BCM numbering)
        valid_pins = list(range(2, 28))  # GPIO 2-27
        if value not in valid_pins:
            raise ValidationError(f"{name} must be a valid GPIO pin (2-27)")
    
    @staticmethod
    def _is_valid_websocket_url(url: str) -> bool:
        """Check if a URL is a valid WebSocket URL."""
        websocket_pattern = re.compile(
            r'^(wss?:\/\/)'  # ws:// or wss://
            r'((([A-Za-z0-9-]+\.)+[A-Za-z]{2,})|'  # domain...
            r'localhost|'  # localhost...
            r'(\d{1,3}\.){3}\d{1,3})'  # ...or ip
            r'(:\d+)?'  # optional port
            r'(\/[A-Za-z0-9\-._~:\/?#\[\]@!$&\'()*+,;=]*)?$'  # optional path
        )
        return bool(websocket_pattern.match(url))