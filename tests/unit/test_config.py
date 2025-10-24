"""
Unit tests for configuration management.

This module tests the configuration manager and related functionality.
"""

import pytest
import os
import tempfile
from unittest.mock import patch, mock_open

from bitchat.config.manager import ConfigManager
from bitchat.config.validation import ConfigValidator
from bitchat.exceptions import ConfigurationError


@pytest.mark.unit
class TestConfigManager:
    """Test cases for ConfigManager."""
    
    def test_init_with_default_config(self, config_file):
        """Test initialization with default configuration."""
        manager = ConfigManager(config_file)
        
        # Check that default values are loaded
        assert manager.get("application.name") == "blue-relay-chat"
        assert manager.get("application.version") == "0.1.0-test"
        assert manager.get("application.debug") is False
        assert manager.get("application.log_level") == "DEBUG"
    
    def test_init_with_custom_config(self, config_file):
        """Test initialization with custom configuration."""
        # Create a custom config file
        with open(config_file, 'w') as f:
            f.write("""
[application]
name = custom-app
version = 1.0.0
debug = true
log_level = INFO

[storage]
data_dir = /custom/data
database_file = custom.db
            """)
        
        manager = ConfigManager(config_file)
        
        # Check that custom values are loaded
        assert manager.get("application.name") == "custom-app"
        assert manager.get("application.version") == "1.0.0"
        assert manager.get("application.debug") is True
        assert manager.get("application.log_level") == "INFO"
        assert manager.get("storage.data_dir") == "/custom/data"
        assert manager.get("storage.database_file") == "custom.db"
    
    def test_get_existing_config(self, config_manager):
        """Test getting existing configuration values."""
        # Test getting a value that exists
        assert config_manager.get("application.name") == "blue-relay-chat"
        
        # Test getting a value that doesn't exist (should return default)
        assert config_manager.get("nonexistent.key", "default") == "default"
        
        # Test getting a value with a different default
        assert config_manager.get("nonexistent.key", "custom_default") == "custom_default"
    
    def test_set_config_value(self, config_manager):
        """Test setting a configuration value."""
        # Set a value
        config_manager.set("test.key", "test_value")
        
        # Check that the value was set
        assert config_manager.get("test.key") == "test_value"
        
        # Set a nested value
        config_manager.set("test.nested.key", "nested_value")
        assert config_manager.get("test.nested.key") == "nested_value"
    
    def test_reload_config(self, config_manager, config_file):
        """Test reloading configuration."""
        # Modify the config file
        with open(config_file, 'a') as f:
            f.write("\n[reload_test]\nvalue = reloaded\n")
        
        # Reload the configuration
        config_manager.reload()
        
        # Check that the new value was loaded
        assert config_manager.get("reload_test.value") == "reloaded"
    
    def test_get_data_dir(self, config_manager):
        """Test getting the data directory."""
        data_dir = config_manager.get_data_dir()
        
        # Check that it's a valid path
        assert os.path.isdir(data_dir)
        
        # Check that it ends with the expected directory name
        assert data_dir.endswith("blue-relay-chat")
    
    def test_get_database_path(self, config_manager):
        """Test getting the database path."""
        db_path = config_manager.get_database_path()
        
        # Check that it's a valid path
        assert os.path.dirname(db_path) == config_manager.get_data_dir()
        assert db_path.endswith("blue-relay-chat.db")
    
    def test_get_nostr_relays(self, config_manager):
        """Test getting Nostr relay configuration."""
        relays = config_manager.get_nostr_relays()
        
        # Check that it's a list
        assert isinstance(relays, list)
        
        # Check that it contains the expected default relays
        assert "wss://relay.example.com" in relays
        assert "wss://relay2.example.com" in relays
    
    def test_config_validation(self, config_manager):
        """Test configuration validation."""
        # Create a validator
        validator = ConfigValidator()
        
        # Validate the current configuration
        errors = validator.validate(config_manager._config)
        
        # Check that there are no validation errors
        assert len(errors) == 0


@pytest.mark.unit
class TestConfigValidator:
    """Test cases for ConfigValidator."""
    
    def test_validate_valid_config(self):
        """Test validation of a valid configuration."""
        validator = ConfigValidator()
        
        # Valid configuration
        config = {
            "application": {
                "name": "test-app",
                "version": "1.0.0",
                "debug": False,
                "log_level": "INFO",
            },
            "storage": {
                "data_dir": "/tmp/test",
                "database_file": "test.db",
                "max_message_history": 1000,
                "auto_cleanup": True,
                "cleanup_interval_hours": 24,
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
                "relays": ["wss://relay.example.com"],
                "max_relay_connections": 5,
                "subscription_limit": 10,
                "event_batch_size": 50,
                "connection_timeout_seconds": 15,
                "reconnect_interval_seconds": 30,
            },
            "security": {
                "encryption_algorithm": "ChaCha20-Poly1305",
                "key_derivation_iterations": 100000,
                "encrypt_private_keys": False,
                "emergency_wipe_confirmations": 3,
                "emergency_wipe_gpio": 18,
            },
            "network": {
                "max_retries": 3,
                "retry_delay_seconds": 5,
            },
            "performance": {
                "message_queue_size": 1000,
                "max_concurrent_connections": 10,
            },
            "cli": {
                "refresh_rate_ms": 100,
                "max_display_lines": 1000,
                "timestamp_format": "%H:%M:%S",
                "show_system_messages": True,
                "auto_scroll": True,
            },
        }
        
        # Validate the configuration
        errors = validator.validate(config)
        
        # Check that there are no validation errors
        assert len(errors) == 0
    
    def test_validate_invalid_config(self):
        """Test validation of an invalid configuration."""
        validator = ConfigValidator()
        
        # Invalid configuration (missing required fields)
        config = {
            "application": {
                # Missing name
                "version": "1.0.0",
                "debug": False,
                "log_level": "INFO",
            },
            "storage": {
                # Invalid data_dir (not a string)
                "data_dir": 123,
                "database_file": "test.db",
                # Invalid max_message_history (not a positive integer)
                "max_message_history": -100,
                # Invalid cleanup_interval_hours (not a positive integer)
                "cleanup_interval_hours": 0,
            },
            "bluetooth": {
                # Invalid scan_interval_seconds (not a positive integer)
                "adapter_name": "hci0",
                "scan_interval_seconds": -5,
                # Invalid mesh_ttl (not in valid range)
                "mesh_ttl": 0,
            },
            "nostr": {
                # Invalid relays (not a list)
                "relays": "not-a-list",
                # Invalid max_relay_connections (not a positive integer)
                "max_relay_connections": 0,
            },
            "security": {
                # Invalid encryption_algorithm (not supported)
                "encryption_algorithm": "invalid-algorithm",
                # Invalid key_derivation_iterations (not a positive integer)
                "key_derivation_iterations": 0,
            },
            "network": {
                # Invalid max_retries (not a positive integer)
                "max_retries": 0,
                # Invalid retry_delay_seconds (not a positive number)
                "retry_delay_seconds": -1,
            },
            "performance": {
                # Invalid message_queue_size (not a positive integer)
                "message_queue_size": 0,
                # Invalid max_concurrent_connections (not a positive integer)
                "max_concurrent_connections": 0,
            },
            "cli": {
                # Invalid refresh_rate_ms (not a positive integer)
                "refresh_rate_ms": 0,
                # Invalid max_display_lines (not a positive integer)
                "max_display_lines": 0,
                # Invalid timestamp_format (not a valid format)
                "timestamp_format": "invalid-format",
            },
        }
        
        # Validate the configuration
        errors = validator.validate(config)
        
        # Check that there are validation errors
        assert len(errors) > 0
        
        # Check for specific expected errors
        error_keys = [error.key for error in errors]
        assert "application.name" in error_keys  # Missing required field
        assert "storage.data_dir" in error_keys  # Invalid type
        assert "storage.max_message_history" in error_keys  # Invalid value
        assert "bluetooth.scan_interval_seconds" in error_keys  # Invalid value
        assert "bluetooth.mesh_ttl" in error_keys  # Invalid value
        assert "nostr.relays" in error_keys  # Invalid type
        assert "security.encryption_algorithm" in error_keys  # Invalid value
        assert "network.max_retries" in error_keys  # Invalid value
        assert "performance.message_queue_size" in error_keys  # Invalid value
        assert "cli.refresh_rate_ms" in error_keys  # Invalid value
        assert "cli.timestamp_format" in error_keys  # Invalid value


@pytest.mark.unit
class TestConfigIntegration:
    """Integration tests for configuration management."""
    
    def test_config_with_environment_variables(self, monkeypatch):
        """Test configuration with environment variables."""
        # Set environment variables
        monkeypatch.setenv("BRC_DEBUG", "true")
        monkeypatch.setenv("BRC_LOG_LEVEL", "WARNING")
        monkeypatch.setenv("BRC_DATA_DIR", "/env/test/data")
        
        # Create a temporary config file
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write("""
[application]
name = env-test-app
version = 1.0.0
debug = false
log_level = INFO

[storage]
data_dir = ~/.local/share/blue-relay-chat
database_file = env-test.db
            """)
            
            # Initialize config manager
            manager = ConfigManager(f.name)
            
            # Check that environment variables override config file
            assert manager.get("application.debug") is True  # From BRC_DEBUG
            assert manager.get("application.log_level") == "WARNING"  # From BRC_LOG_LEVEL
            assert manager.get("storage.data_dir") == "/env/test/data"  # From BRC_DATA_DIR
            
            # Check that config file values are still accessible
            assert manager.get("application.name") == "env-test-app"
            assert manager.get("storage.database_file") == "env-test.db"
    
    def test_config_with_command_line_args(self, monkeypatch):
        """Test configuration with command line arguments."""
        # Mock sys.argv
        monkeypatch.setattr("sys.argv", [
            "test_script.py",
            "--name", "cli-test-app",
            "--debug",
            "--data-dir", "/cli/test/data",
            "--log-level", "ERROR"
        ])
        
        # Initialize config manager
        manager = ConfigManager()
        
        # Check that command line args override config file
        assert manager.get("application.name") == "cli-test-app"
        assert manager.get("application.debug") is True  # From --debug
        assert manager.get("application.log_level") == "ERROR"  # From --log-level
        assert manager.get("storage.data_dir") == "/cli/test/data"  # From --data-dir