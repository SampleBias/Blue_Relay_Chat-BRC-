"""
Pytest configuration and fixtures for Blue Relay Chat tests.

This module provides common fixtures and configuration for the test suite.
"""

import os
import sys
import pytest
import tempfile
import shutil
from unittest.mock import MagicMock, AsyncMock
from pathlib import Path

# Add the parent directory to the path so we can import the modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from bitchat.config.manager import ConfigManager
from bitchat.security.crypto import CryptoManager
from bitchat.security.identity import IdentityManager
from bitchat.data.database import DatabaseManager
from bitchat.core.events import EventBus
from bitchat.core.router import MessageRouter
from bitchat.data.queue import MessageQueue


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    import asyncio
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def temp_dir():
    """Create a temporary directory for tests."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
def config_file(temp_dir):
    """Create a temporary config file for tests."""
    config_path = os.path.join(temp_dir, "test_config.ini")
    
    # Create a basic config file
    with open(config_path, "w") as f:
        f.write("""
[application]
name = blue-relay-chat
version = 0.1.0-test
debug = true
log_level = DEBUG

[storage]
data_dir = {temp_dir}
database_file = test.db
max_message_history = 100
auto_cleanup = false

[bluetooth]
adapter_name = hci0
scan_interval_seconds = 5
advertisement_interval_seconds = 5
max_peers = 10
mesh_ttl = 5
discovery_timeout_seconds = 10
power_save_mode = false

[nostr]
relays = wss://relay1.example.com,wss://relay2.example.com
max_relay_connections = 3
subscription_limit = 5
event_batch_size = 10
connection_timeout_seconds = 5
reconnect_interval_seconds = 10

[security]
encryption_algorithm = ChaCha20-Poly1305
key_derivation_iterations = 1000
encrypt_private_keys = false
emergency_wipe_confirmations = 1
emergency_wipe_gpio = 18

[network]
max_retries = 3
retry_delay_seconds = 1

[performance]
message_queue_size = 100
max_concurrent_connections = 10

[cli]
refresh_rate_ms = 50
max_display_lines = 50
timestamp_format = %H:%M:%S
show_system_messages = true
auto_scroll = true
        """.format(temp_dir=temp_dir))
    
    return config_path


@pytest.fixture
def config_manager(config_file):
    """Create a ConfigManager instance for tests."""
    return ConfigManager(config_file)


@pytest.fixture
def crypto_manager(config_manager):
    """Create a CryptoManager instance for tests."""
    return CryptoManager(config_manager)


@pytest.fixture
def identity_manager(config_manager, crypto_manager):
    """Create an IdentityManager instance for tests."""
    manager = IdentityManager(config_manager)
    
    # Override the crypto manager for testing
    manager.crypto = crypto_manager
    
    return manager


@pytest.fixture
def database_manager(config_manager, temp_dir):
    """Create a DatabaseManager instance for tests."""
    # Override the database path for testing
    config_manager._config["storage"]["database_file"] = "test.db"
    config_manager._config["storage"]["data_dir"] = temp_dir
    
    manager = DatabaseManager(config_manager)
    
    # Initialize the database
    import asyncio
    loop = asyncio.get_event_loop()
    loop.run_until_complete(manager.initialize())
    
    yield manager
    
    # Clean up
    loop.run_until_complete(manager.disconnect())


@pytest.fixture
def event_bus():
    """Create an EventBus instance for tests."""
    return EventBus()


@pytest.fixture
def message_router(config_manager, event_bus, database_manager):
    """Create a MessageRouter instance for tests."""
    router = MessageRouter(config_manager, event_bus)
    
    # Override the database manager for testing
    router.db = database_manager
    
    return router


@pytest.fixture
def message_queue(config_manager, database_manager):
    """Create a MessageQueue instance for tests."""
    queue = MessageQueue(config_manager, database_manager)
    
    # Initialize the queue
    import asyncio
    loop = asyncio.get_event_loop()
    loop.run_until_complete(queue.initialize())
    
    yield queue
    
    # Clean up
    loop.run_until_complete(queue.stop_processing())


@pytest.fixture
def mock_bluetooth_device():
    """Create a mock Bluetooth device for tests."""
    device = MagicMock()
    device.address = "00:11:22:33:44:55"
    device.name = "Test Device"
    device.rssi = -50
    
    # Add service UUIDs
    device.metadata = {"uuids": ["12345678-1234-1234-1234-123456789abc"]}
    
    return device


@pytest.fixture
def mock_nostr_relay():
    """Create a mock Nostr relay for tests."""
    relay = MagicMock()
    relay.url = "wss://relay.example.com"
    relay.connected = True
    
    return relay


@pytest.fixture
def sample_message():
    """Create a sample message for tests."""
    return {
        "id": "test-message-123",
        "sender_id": "test-sender-456",
        "recipient_id": "test-recipient-789",
        "content": "This is a test message",
        "message_type": "text",
        "transport_type": "mesh",
        "created_at": "2023-01-01T00:00:00",
        "status": "pending",
        "encrypted": False,
        "compressed": False,
        "metadata": {}
    }


@pytest.fixture
def sample_peer():
    """Create a sample peer for tests."""
    return {
        "id": "test-peer-123",
        "public_key": "test-public-key-456",
        "last_seen": "2023-01-01T00:00:00",
        "transport_type": "mesh",
        "is_local": True,
        "status": "online",
        "metadata": {}
    }


@pytest.fixture
def sample_channel():
    """Create a sample channel for tests."""
    return {
        "id": "test-channel-123",
        "name": "Test Channel",
        "channel_type": "mesh",
        "is_private": False,
        "created_at": "2023-01-01T00:00:00",
        "description": "A test channel",
        "metadata": {}
    }


@pytest.fixture
def mock_event_bus():
    """Create a mock EventBus for tests."""
    bus = AsyncMock(spec=EventBus)
    
    # Mock the publish method
    async def mock_publish(event):
        pass
    
    bus.publish = mock_publish
    
    return bus


@pytest.fixture
def mock_transport():
    """Create a mock transport for tests."""
    from bitchat.constants import TransportType
    
    transport = MagicMock()
    transport.transport_type = TransportType.MESH
    transport.is_connected = True
    transport.is_running = True
    
    # Mock async methods
    transport.start = AsyncMock()
    transport.stop = AsyncMock()
    transport.send_message = AsyncMock(return_value=True)
    transport.get_connected_peers = AsyncMock(return_value={})
    transport.get_transport_info = AsyncMock(return_value={})
    
    return transport


@pytest.fixture
def mock_crypto_manager():
    """Create a mock CryptoManager for tests."""
    crypto = MagicMock(spec=CryptoManager)
    
    # Mock methods
    crypto.generate_key = MagicMock(return_value=b"test-key-32-bytes-long")
    crypto.generate_nonce = MagicMock(return_value=b"test-nonce-12")
    crypto.encrypt = MagicMock(return_value=(b"encrypted-data", b"nonce"))
    crypto.decrypt = MagicMock(return_value=b"decrypted-data")
    crypto.generate_ed25519_keypair = MagicMock(return_value=(b"private-key", b"public-key"))
    crypto.sign_message = MagicMock(return_value=b"signature")
    crypto.verify_signature = MagicMock(return_value=True)
    
    return crypto


@pytest.fixture
def mock_identity():
    """Create a mock identity for tests."""
    from bitchat.data.models import Identity
    
    identity = MagicMock(spec=Identity)
    identity.id = "test-identity-123"
    identity.public_key = "test-public-key-456"
    identity.private_key = "test-private-key-789"
    identity.key_algorithm = "ed25519"
    identity.created_at = "2023-01-01T00:00:00"
    identity.last_used = "2023-01-01T00:00:00"
    identity.metadata = {}
    
    return identity


# Test markers
pytest.mark.unit = pytest.mark.unit
pytest.mark.integration = pytest.mark.integration
pytest.mark.slow = pytest.mark.slow
pytest.mark.bluetooth = pytest.mark.bluetooth
pytest.mark.nostr = pytest.mark.nostr
pytest.mark.security = pytest.mark.security
pytest.mark.cli = pytest.mark.cli


# Skip tests that require hardware
def pytest_configure(config):
    config.addinivalue_line(
        "markers", "skip_hardware: mark test to be skipped when hardware is not available"
    )
    config.addinivalue_line(
        "markers", "skip_network: mark test to be skipped when network is not available"
    )


def pytest_collection_modifyitems(config, items):
    """Add custom markers to tests."""
    import os
    
    # Skip hardware tests if not on a Raspberry Pi
    if not os.path.exists("/proc/device-tree/model") or "raspberry pi" not in open("/proc/device-tree/model").read().lower():
        skip_hardware = pytest.mark.skip(reason="Hardware test skipped (not on Raspberry Pi)")
        for item in items:
            if "hardware" in item.keywords:
                item.add_marker(skip_hardware)
    
    # Skip network tests if network is not available
    try:
        import socket
        socket.create_connection(("8.8.8.8"), 53)
    except:
        skip_network = pytest.mark.skip(reason="Network test skipped (no network connection)")
        for item in items:
            if "network" in item.keywords:
                item.add_marker(skip_network)