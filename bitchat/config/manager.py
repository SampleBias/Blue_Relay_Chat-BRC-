
"""
Configuration manager for bitchat RPi 4 client.

This module provides the main configuration management functionality,
including loading from files, environment variables, and providing
access to configuration values throughout the application.
"""

import os
import configparser
from typing import Any, Dict, List, Optional, Union
from pathlib import Path

from ..exceptions import ConfigurationError
from .defaults import DEFAULT_CONFIG
from .validation import ConfigValidator
from ..utils.hardware_detection import get_hardware_detector


class ConfigManager:
    """Manages application configuration from multiple sources."""
    
    def __init__(self, config_file: Optional[str] = None) -> None:
        """
        Initialize the configuration manager.
        
        Args:
            config_file: Path to configuration file. If None, uses default locations.
        """
        self._config: Dict[str, Dict[str, Any]] = {}
        self._config_file = config_file or self._find_config_file()
        self._validator = ConfigValidator()
        self._hardware_detector = get_hardware_detector()
        
        # Load configuration from all sources
        self._load_configuration()
        
        # Validate the final configuration
        self._validate_configuration()
    
    def _find_config_file(self) -> str:
        """Find the configuration file in standard locations."""
        possible_locations = [
            os.path.expanduser("~/.config/blue-relay-chat/config.ini"),
            os.path.expanduser("~/.blue-relay-chat/config.ini"),
            "/etc/blue-relay-chat/config.ini",
            "config.ini",  # Current directory
        ]
        
        for location in possible_locations:
            if os.path.exists(location):
                return location
        
        # If no config file found, return the default location
        return os.path.expanduser("~/.config/blue-relay-chat/config.ini")
    
    def _load_configuration(self) -> None:
        """Load configuration from all sources."""
        # Start with defaults
        self._config = DEFAULT_CONFIG.copy()
        
        # Load from file if it exists
        if os.path.exists(self._config_file):
            self._load_from_file()
        
        # Override with environment variables
        self._load_from_environment()
        
        # Apply hardware-specific overrides
        self._apply_hardware_overrides()
    
    def _load_from_file(self) -> None:
        """Load configuration from INI file."""
        try:
            # Use a parser with no interpolation to avoid issues with %H:%M:%S
            parser = configparser.ConfigParser(interpolation=None)
            parser.read(self._config_file)
            
            # Convert INI format to nested dictionary
            for section_name in parser.sections():
                if section_name not in self._config:
                    self._config[section_name] = {}
                
                for key, value in parser[section_name].items():
                    self._config[section_name][key] = self._parse_value(value)
            
        except configparser.Error as e:
            raise ConfigurationError(f"Error reading configuration file {self._config_file}: {e}")
    
    def _load_from_environment(self) -> None:
        """Load configuration from environment variables."""
        env_prefix = "BITCHAT_"
        
        for env_var, env_value in os.environ.items():
            if not env_var.startswith(env_prefix):
                continue
            
            # Remove prefix and convert to lowercase
            config_key = env_var[len(env_prefix):].lower()
            
            # Split into section and key
            if "_" in config_key:
                section, key = config_key.split("_", 1)
            else:
                section, key = "application", config_key
            
            # Ensure section exists
            if section not in self._config:
                self._config[section] = {}
            
            # Parse and set the value
            self._config[section][key] = self._parse_value(env_value)
    
    def _parse_value(self, value: str) -> Union[str, int, float, bool, List[str]]:
        """
        Parse a string value to the appropriate type.
        
        Args:
            value: String value to parse
            
        Returns:
            Parsed value (str, int, float, bool, or list)
        """
        # Handle boolean values
        if value.lower() in ("true", "yes", "1", "on"):
            return True
        elif value.lower() in ("false", "no", "0", "off"):
            return False
        
        # Handle integer values
        try:
            return int(value)
        except ValueError:
            pass
        
        # Handle float values
        try:
            return float(value)
        except ValueError:
            pass
        
        # Handle comma-separated lists
        if "," in value:
            return [item.strip() for item in value.split(",")]
        
        # Default to string
        return value
    
    def _apply_hardware_overrides(self) -> None:
        """Apply hardware-specific configuration overrides."""
        try:
            hardware_info = self._hardware_detector.get_hardware_info()
            
            # Apply RPi Zero 2W specific overrides
            if hardware_info.get("device_type") == "rpi_zero_2w":
                self._apply_rpi_zero_2w_overrides()
            
            # Apply laptop specific overrides
            elif hardware_info.get("device_type") == "laptop":
                self._apply_laptop_overrides()
            
        except Exception as e:
            self.logger.warning(f"Failed to apply hardware overrides: {e}")
    
    def _apply_rpi_zero_2w_overrides(self) -> None:
        """Apply RPi Zero 2W specific configuration overrides."""
        # GPIO pin configuration
        self._config["gpio"] = {
            "mode": "BCM",
            "pull_up_down": "PUD_UP",
            "edge": "FALLING",
            "emergency_wipe_gpio": 18
        }
        
        # Performance settings
        self._config["performance"] = {
            "max_cpu_usage": 70,
            "max_memory_mb": 100,
            "message_queue_size": 100,
            "gui_update_interval_ms": 100
        }
        
        # Display settings
        self._config["small_screen_gui"] = {
            "screen_width": 128,
            "screen_height": 128,
            "font_width": 6,
            "font_height": 8,
            "max_display_lines": 10,
            "auto_refresh_interval_ms": 500,
            "show_cursor": True
        }
        
        # Bluetooth settings
        self._config["bluetooth"] = {
            "adapter_name": "hci0",
            "scan_interval_seconds": 10,
            "advertisement_interval_seconds": 5,
            "max_peers": 50,
            "mesh_ttl": 7,
            "discovery_timeout_seconds": 30,
            "power_save_mode": True
        }
    
    def _apply_laptop_overrides(self) -> None:
        """Apply laptop specific configuration overrides."""
        # GUI settings
        self._config["laptop_gui"] = {
            "window_width": 600,
            "window_height": 400,
            "min_window_width": 400,
            "min_window_height": 300,
            "auto_scroll": True,
            "max_message_history": 1000,
            "font_family": "TkDefaultFont",
            "font_size": 10,
            "theme": "light",
            "show_timestamps": True,
            "compact_mode": False
        }
        
        # Bluetooth settings
        self._config["laptop_bluetooth"] = {
            "adapter_name": "auto",
            "scan_interval_seconds": 30,
            "max_peers": 20,
            "auto_reconnect": True,
            "connection_timeout_seconds": 10,
            "discovery_timeout_seconds": 30,
            "power_save_mode": False
        }
        
        # Performance settings
        self._config["performance"] = {
            "max_cpu_usage": 30,
            "max_memory_mb": 200,
            "message_queue_size": 500,
            "gui_update_interval_ms": 100
        }
    
    def _validate_configuration(self) -> None:
        """Validate the loaded configuration."""
        try:
            for section_name, section_config in self._config.items():
                self._validator.validate_section(section_name, section_config)
        except Exception as e:
            raise ConfigurationError(f"Configuration validation failed: {e}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a configuration value.
        
        Args:
            key: Configuration key in format "section.key" or just "key" for application section
            default: Default value if key is not found
            
        Returns:
            Configuration value or default
        """
        if "." in key:
            section, config_key = key.split(".", 1)
        else:
            section, config_key = "application", key
        
        return self._config.get(section, {}).get(config_key, default)
    
    def set(self, key: str, value: Any) -> None:
        """
        Set a configuration value.
        
        Args:
            key: Configuration key in format "section.key" or just "key" for application section
            value: Value to set
        """
        if "." in key:
            section, config_key = key.split(".", 1)
        else:
            section, config_key = "application", key
        
        # Ensure section exists
        if section not in self._config:
            self._config[section] = {}
        
        # Set the value
        self._config[section][config_key] = value
    
    def get_section(self, section: str) -> Dict[str, Any]:
        """
        Get an entire configuration section.
        
        Args:
            section: Section name
            
        Returns:
            Dictionary of section configuration
        """
        return self._config.get(section, {}).copy()
    
    def has(self, key: str) -> bool:
        """
        Check if a configuration key exists.
        
        Args:
            key: Configuration key in format "section.key" or just "key" for application section
            
        Returns:
            True if key exists, False otherwise
        """
        if "." in key:
            section, config_key = key.split(".", 1)
        else:
            section, config_key = "application", key
        
        return section in self._config and config_key in self._config[section]
    
    def save(self, file_path: Optional[str] = None) -> None:
        """
        Save configuration to file.
        
        Args:
            file_path: Path to save configuration. If None, uses current config file.
        """
        save_path = file_path or self._config_file
        
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        
        # Create parser and write configuration
        parser = configparser.ConfigParser()
        
        # Convert configuration to INI format
        for section_name, section_config in self._config.items():
            parser[section_name] = {}
            for key, value in section_config.items():
                # Convert value back to string
                if isinstance(value, list):
                    str_value = ",".join(value)
                elif isinstance(value, bool):
                    str_value = "true" if value else "false"
                else:
                    str_value = str(value)
                
                parser[section_name][key] = str_value
        
        # Write to file
        try:
            with open(save_path, "w") as f:
                parser.write(f)
            self._config_file = save_path
        except IOError as e:
            raise ConfigurationError(f"Error saving configuration to {save_path}: {e}")
    
    def reload(self) -> None:
        """Reload configuration from sources."""
        self._load_configuration()
        self._validate_configuration()
    
    def get_data_dir(self) -> str:
        """Get the data directory path, expanded and created if necessary."""
        data_dir = self.get("storage.data_dir", "~/.local/share/blue-relay-chat")
        expanded_dir = os.path.expanduser(data_dir)
        
        # Create directory if it doesn't exist
        os.makedirs(expanded_dir, exist_ok=True)
        
        return expanded_dir
    
    def get_database_path(self) -> str:
        """Get the full path to the database file."""
        data_dir = self.get_data_dir()
        db_file = self.get("storage.database_file", "blue-relay-chat.db")
        return os.path.join(data_dir, db_file)
    
    def get_log_level(self) -> str:
        """Get the log level as a string."""
        return self.get("application.log_level", "INFO").upper()
    
    def is_debug_mode(self) -> bool:
        """Check if debug mode is enabled."""
        return self.get("application.debug", False)
    
    def get_nostr_relays(self) -> List[str]:
        """Get the list of Nostr relay URLs."""
        relays = self.get("nostr.relays", 
                               "wss://relay.damus.io,wss://nos.lol,wss://relay.snort.social")
        
        if isinstance(relays, str):
            return [relay.strip() for relay in relays.split(",")]
        elif isinstance(relays, list):
            return relays
        else:
            return []
    
    def is_laptop_mode(self) -> bool:
        """Check if running in laptop mode."""
        return self.get("application.mode", "") == "laptop"
    
    def is_small_screen_mode(self) -> bool:
        """Check if running in small screen mode."""
        return self.get("application.mode", "") == "small_screen"
    
    def is_rpi_zero_2w_mode(self) -> bool:
        """Check if running in RPi Zero 2W mode."""
        return self.get("application.mode", "") == "rpi_zero_2w"
    
    def get_platform_config(self) -> Dict[str, Any]:
        """Get platform-specific configuration."""
        return self._config.get("platform", {})
    
    def get_hardware_info(self) -> Dict[str, Any]:
        """Get hardware information."""
        return self._hardware_detector.get_hardware_info()
    
    def __repr__(self) -> str:
        """String representation of the configuration manager."""
        return f"ConfigManager(config_file={self._config_file})"