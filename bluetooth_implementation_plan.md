# Bluetooth Communication Implementation Plan

## Overview

This document outlines the implementation of Bluetooth communication for the laptop client, ensuring cross-platform compatibility with Windows, macOS, and Linux systems.

## Cross-Platform Bluetooth Architecture

### Platform-Specific Considerations

#### Windows
- **API**: Windows Bluetooth APIs via bleak library
- **Requirements**: Windows 10/11 with Bluetooth support
- **Permissions**: Administrator privileges may be required for some operations
- **Features**: Supports BLE and Classic Bluetooth

#### macOS
- **API**: Core Bluetooth framework via bleak library
- **Requirements**: macOS 10.10+ with Bluetooth support
- **Permissions**: Bluetooth usage entitlement in app bundle
- **Features**: Excellent BLE support, limited Classic Bluetooth

#### Linux
- **API**: BlueZ via bleak library
- **Requirements**: Linux with BlueZ 5.0+ and Bluetooth adapter
- **Permissions**: User in bluetooth group or appropriate D-Bus permissions
- **Features**: Full BLE and Classic Bluetooth support

## Implementation Details

### 1. Laptop Bluetooth Manager (`bitchat/transports/laptop_bluetooth.py`)

```python
import asyncio
import platform
import struct
import uuid
from typing import Dict, Any, Optional, List, Set
from datetime import datetime
import logging

import bleak
from bleak import BleakScanner, BleakClient
from bleak.backends.device import BLEDevice
from bleak.exc import BleakError

from ...config.manager import ConfigManager
from ...utils.logging import get_logger
from ...constants import TransportType, DEFAULT_MESH_TTL
from ...exceptions import BluetoothError, TransportError
from ..base import BaseTransport, TransportStatus
from .mesh_protocol import MeshProtocol

class LaptopBluetoothTransport(BaseTransport):
    """Cross-platform Bluetooth LE transport for laptop client."""
    
    # Bluetooth service and characteristic UUIDs for BRC
    SERVICE_UUID = uuid.UUID("12345678-1234-1234-1234-123456789abc")
    MESSAGE_CHAR_UUID = uuid.UUID("12345678-1234-1234-1234-123456789abd")
    CONTROL_CHAR_UUID = uuid.UUID("12345678-1234-1234-1234-123456789abe")
    
    def __init__(self, config_manager: ConfigManager) -> None:
        """
        Initialize the laptop Bluetooth transport.
        
        Args:
            config_manager: Configuration manager instance
        """
        super().__init__(config_manager, TransportType.MESH)
        
        # Platform detection
        self.platform = platform.system().lower()
        self.logger = get_logger("laptop_bluetooth")
        
        # Bluetooth configuration
        self.adapter_name = config_manager.get("bluetooth.adapter_name", "auto")
        self.scan_interval = config_manager.get("bluetooth.scan_interval_seconds", 30)
        self.max_peers = config_manager.get("bluetooth.max_peers", 20)
        self.auto_reconnect = config_manager.get("bluetooth.auto_reconnect", True)
        self.connection_timeout = config_manager.get("bluetooth.connection_timeout_seconds", 10)
        self.discovery_timeout = config_manager.get("bluetooth.discovery_timeout_seconds", 30)
        
        # Platform-specific initialization
        self._initialize_platform_specific()
        
        # Bluetooth components
        self.scanner: Optional[BleakScanner] = None
        self.mesh_protocol = MeshProtocol(config_manager)
        
        # Connection state
        self._connected_devices: Dict[str, BleakClient] = {}
        self._device_info: Dict[str, Dict[str, Any]] = {}
        self._scan_task: Optional[asyncio.Task] = None
        self._reconnect_tasks: Dict[str, asyncio.Task] = {}
        
        # Message handling
        self._message_handlers: Dict[str, callable] = {}
        self._pending_messages: Dict[str, asyncio.Future] = {}
    
    def _initialize_platform_specific(self) -> None:
        """Initialize platform-specific Bluetooth settings."""
        if self.platform == "windows":
            self._init_windows_bluetooth()
        elif self.platform == "darwin":  # macOS
            self._init_macos_bluetooth()
        elif self.platform == "linux":
            self._init_linux_bluetooth()
        else:
            self.logger.warning(f"Unsupported platform: {self.platform}")
    
    def _init_windows_bluetooth(self) -> None:
        """Initialize Windows-specific Bluetooth settings."""
        self.logger.info("Initializing Windows Bluetooth")
        # Windows-specific initialization
        # May need to check for Windows Bluetooth driver support
        
    def _init_macos_bluetooth(self) -> None:
        """Initialize macOS-specific Bluetooth settings."""
        self.logger.info("Initializing macOS Bluetooth")
        # macOS-specific initialization
        # Core Bluetooth framework initialization
        
    def _init_linux_bluetooth(self) -> None:
        """Initialize Linux-specific Bluetooth settings."""
        self.logger.info("Initializing Linux Bluetooth")
        # Linux-specific initialization
        # BlueZ adapter detection and configuration
```

### 2. Device Discovery Implementation

```python
async def _do_start(self) -> None:
    """Start the Bluetooth transport with platform-specific setup."""
    try:
        # Check platform compatibility
        if not await self._check_platform_support():
            raise BluetoothError(f"Bluetooth not supported on {self.platform}")
        
        # Initialize scanner with platform-specific settings
        await self._initialize_scanner()
        
        # Start device discovery
        await self._start_discovery()
        
        # Set up message handlers
        self._setup_message_handlers()
        
        await self._set_status(TransportStatus.CONNECTED)
        self.logger.info(f"Laptop Bluetooth transport started on {self.platform}")
        
    except Exception as e:
        self.logger.error(f"Failed to start Bluetooth transport: {e}")
        raise BluetoothError(f"Bluetooth transport start failed: {e}")

async def _check_platform_support(self) -> bool:
    """Check if Bluetooth is supported on the current platform."""
    try:
        if self.platform == "windows":
            return await self._check_windows_bluetooth()
        elif self.platform == "darwin":
            return await self._check_macos_bluetooth()
        elif self.platform == "linux":
            return await self._check_linux_bluetooth()
        else:
            return False
    except Exception as e:
        self.logger.error(f"Error checking platform support: {e}")
        return False

async def _check_windows_bluetooth(self) -> bool:
    """Check Windows Bluetooth support."""
    try:
        # Check if Bluetooth radio is available
        import subprocess
        result = subprocess.run(
            ["powershell", "Get-BluetoothDevice"], 
            capture_output=True, 
            text=True
        )
        return result.returncode == 0
    except Exception as e:
        self.logger.warning(f"Could not check Windows Bluetooth: {e}")
        return True  # Assume available if we can't check

async def _check_macos_bluetooth(self) -> bool:
    """Check macOS Bluetooth support."""
    try:
        import subprocess
        result = subprocess.run(
            ["system_profiler", "SPBluetoothDataType"], 
            capture_output=True, 
            text=True
        )
        return "Bluetooth" in result.stdout and "Hardware" in result.stdout
    except Exception as e:
        self.logger.warning(f"Could not check macOS Bluetooth: {e}")
        return True  # Assume available if we can't check

async def _check_linux_bluetooth(self) -> bool:
    """Check Linux Bluetooth support."""
    try:
        import subprocess
        result = subprocess.run(
            ["hciconfig"], 
            capture_output=True, 
            text=True
        )
        return result.returncode == 0 and "hci" in result.stdout
    except Exception as e:
        self.logger.warning(f"Could not check Linux Bluetooth: {e}")
        return True  # Assume available if we can't check

async def _initialize_scanner(self) -> None:
    """Initialize the Bluetooth scanner with platform-specific settings."""
    try:
        scanner_kwargs = {
            "detection_callback": self._on_device_detected
        }
        
        # Platform-specific scanner configuration
        if self.platform == "windows":
            scanner_kwargs.update({
                "adapter": self._get_windows_adapter()
            })
        elif self.platform == "darwin":
            scanner_kwargs.update({
                "adapter": self._get_macos_adapter()
            })
        elif self.platform == "linux":
            scanner_kwargs.update({
                "adapter": self._get_linux_adapter()
            })
        
        self.scanner = BleakScanner(**scanner_kwargs)
        self.logger.debug(f"Bluetooth scanner initialized for {self.platform}")
        
    except Exception as e:
        self.logger.error(f"Failed to initialize scanner: {e}")
        raise BluetoothError(f"Scanner initialization failed: {e}")

def _get_windows_adapter(self) -> str:
    """Get Windows Bluetooth adapter name."""
    if self.adapter_name == "auto":
        return None  # Let bleak choose
    return self.adapter_name

def _get_macos_adapter(self) -> str:
    """Get macOS Bluetooth adapter name."""
    if self.adapter_name == "auto":
        return None  # Let bleak choose
    return self.adapter_name

def _get_linux_adapter(self) -> str:
    """Get Linux Bluetooth adapter name."""
    if self.adapter_name == "auto":
        # Try to find first available adapter
        try:
            import subprocess
            result = subprocess.run(
                ["hcitool", "dev"], 
                capture_output=True, 
                text=True
            )
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                for line in lines[1:]:  # Skip header
                    if line.strip():
                        parts = line.split()
                        if len(parts) >= 2:
                            return parts[1]  # Adapter name (hci0, etc.)
        except Exception as e:
            self.logger.warning(f"Could not auto-detect Linux adapter: {e}")
        return "hci0"  # Default fallback
    return self.adapter_name
```

### 3. Device Connection Management

```python
async def _on_device_detected(self, device: BLEakScanner, advertisement_data: bleak.BleakAdvertisementData) -> None:
    """Handle detection of a Bluetooth device."""
    try:
        device_id = device.address
        device_name = device.name or "Unknown"
        
        # Check if this is a BRC device
        if self.SERVICE_UUID in advertisement_data.service_uuids:
            self.logger.debug(f"Detected BRC device: {device_name} ({device_id})")
            
            # Update device info
            self._device_info[device_id] = {
                "name": device_name,
                "address": device.address,
                "rssi": advertisement_data.rssi,
                "last_seen": datetime.now(),
                "manufacturer_data": advertisement_data.manufacturer_data,
                "service_data": advertisement_data.service_data,
                "platform": self.platform
            }
            
            # Try to connect if we have room
            if (device_id not in self._connected_devices and 
                len(self._connected_devices) < self.max_peers):
                asyncio.create_task(self._connect_to_device(device))
            
            # Notify about device discovery
            await self._on_device_discovered(device_id, self._device_info[device_id])
                
    except Exception as e:
        self.logger.error(f"Error handling device detection: {e}")

async def _connect_to_device(self, device: BLEDevice) -> None:
    """Connect to a Bluetooth device with platform-specific handling."""
    try:
        device_id = device.address
        self.logger.info(f"Connecting to device {device.name} ({device_id})")
        
        # Create client with platform-specific timeout
        client_kwargs = {
            "timeout": self.connection_timeout
        }
        
        # Platform-specific connection settings
        if self.platform == "windows":
            client_kwargs.update(self._get_windows_connection_params())
        elif self.platform == "darwin":
            client_kwargs.update(self._get_macos_connection_params())
        elif self.platform == "linux":
            client_kwargs.update(self._get_linux_connection_params())
        
        client = BleakClient(device, **client_kwargs)
        
        # Connect
        await client.connect()
        
        # Check if it has the BRC service
        if self.SERVICE_UUID in await client.get_services():
            # Store connected device
            self._connected_devices[device_id] = client
            
            # Set up notifications
            await self._setup_notifications(client)
            
            # Exchange mesh information
            await self._exchange_mesh_info(client)
            
            # Cancel any reconnect task for this device
            if device_id in self._reconnect_tasks:
                self._reconnect_tasks[device_id].cancel()
                del self._reconnect_tasks[device_id]
            
            # Notify about peer connection
            await self._on_peer_connected(device_id, self._device_info.get(device_id, {}))
            
            self.logger.info(f"Connected to BRC device: {device.name} ({device_id})")
        else:
            # Not a BRC device, disconnect
            await client.disconnect()
            self.logger.debug(f"Device {device.name} is not a BRC device")
                
    except Exception as e:
        self.logger.error(f"Failed to connect to device {device.address}: {e}")
        
        # Schedule reconnection if enabled
        if self.auto_reconnect:
            await self._schedule_reconnect(device.address)

def _get_windows_connection_params(self) -> Dict[str, Any]:
    """Get Windows-specific connection parameters."""
    return {
        # Windows-specific parameters
    }

def _get_macos_connection_params(self) -> Dict[str, Any]:
    """Get macOS-specific connection parameters."""
    return {
        # macOS-specific parameters
    }

def _get_linux_connection_params(self) -> Dict[str, Any]:
    """Get Linux-specific connection parameters."""
    return {
        # Linux-specific parameters
    }

async def _schedule_reconnect(self, device_id: str) -> None:
    """Schedule reconnection to a device."""
    if device_id in self._reconnect_tasks:
        return  # Already scheduled
    
    async def reconnect_task():
        try:
            await asyncio.sleep(5)  # Wait before reconnecting
            
            device_info = self._device_info.get(device_id)
            if device_info and device_id not in self._connected_devices:
                # Create a mock device for reconnection
                device = BLEakDevice(
                    address=device_id,
                    name=device_info.get("name", "Unknown")
                )
                await self._connect_to_device(device)
                
        except asyncio.CancelledError:
            pass
        except Exception as e:
            self.logger.error(f"Reconnection failed for {device_id}: {e}")
        finally:
            if device_id in self._reconnect_tasks:
                del self._reconnect_tasks[device_id]
    
    self._reconnect_tasks[device_id] = asyncio.create_task(reconnect_task())
```

### 4. Message Handling

```python
async def _setup_notifications(self, client: BleakClient) -> None:
    """Set up notifications for message and control characteristics."""
    try:
        # Set up message notifications
        await client.start_notify(
            self.MESSAGE_CHAR_UUID,
            self._on_message_notification
        )
        
        # Set up control notifications
        await client.start_notify(
            self.CONTROL_CHAR_UUID,
            self._on_control_notification
        )
        
        self.logger.debug(f"Notifications set up for device {client.address}")
        
    except Exception as e:
        self.logger.error(f"Failed to set up notifications: {e}")

def _on_message_notification(self, sender: int, data: bytearray) -> None:
    """Handle incoming message notification."""
    try:
        # Parse mesh message
        message = self.mesh_protocol.parse_message(data)
        
        if message:
            # Handle the message
            asyncio.create_task(self._handle_mesh_message(message))
            
    except Exception as e:
        self.logger.error(f"Error handling message notification: {e}")

def _on_control_notification(self, sender: int, data: bytearray) -> None:
    """Handle incoming control notification."""
    try:
        # Parse control message
        control_msg = self.mesh_protocol.parse_control_message(data)
        
        if control_msg:
            # Handle the control message
            asyncio.create_task(self._handle_control_message(control_msg))
            
    except Exception as e:
        self.logger.error(f"Error handling control notification: {e}")

async def _do_send_message(self, message: Dict[str, Any]) -> bool:
    """Send a message via Bluetooth mesh."""
    try:
        # Get message destination
        recipient_id = message.get("recipient_id")
        channel_id = message.get("channel_id")
        
        if recipient_id:
            # Direct message to specific peer
            return await self._send_direct_message(recipient_id, message)
        elif channel_id:
            # Channel message (broadcast to all peers in channel)
            return await self._send_channel_message(channel_id, message)
        else:
            # Broadcast to all connected peers
            return await self._send_broadcast_message(message)
            
    except Exception as e:
        self.logger.error(f"Failed to send Bluetooth message: {e}")
        return False

async def _send_direct_message(self, recipient_id: str, message: Dict[str, Any]) -> bool:
    """Send a direct message to a specific peer."""
    try:
        # Check if recipient is connected
        if recipient_id in self._connected_devices:
            client = self._connected_devices[recipient_id]
            
            # Create mesh message
            mesh_msg = self.mesh_protocol.create_message(message)
            
            # Send message
            await client.write_gatt_char(self.MESSAGE_CHAR_UUID, mesh_msg)
            
            return True
        else:
            # Recipient not connected
            self.logger.warning(f"Recipient {recipient_id} not connected")
            return False
            
    except Exception as e:
        self.logger.error(f"Failed to send direct message to {recipient_id}: {e}")
        return False

async def _send_broadcast_message(self, message: Dict[str, Any]) -> bool:
    """Send a broadcast message to all connected peers."""
    try:
        # Create mesh message
        mesh_msg = self.mesh_protocol.create_broadcast_message(message)
        
        # Send to all connected devices
        success_count = 0
        for device_id, client in self._connected_devices.items():
            try:
                await client.write_gatt_char(self.MESSAGE_CHAR_UUID, mesh_msg)
                success_count += 1
            except Exception as e:
                self.logger.error(f"Failed to send broadcast message to {device_id}: {e}")
        
        return success_count > 0
        
    except Exception as e:
        self.logger.error(f"Failed to send broadcast message: {e}")
        return False
```

### 5. Platform-Specific Utilities

```python
class BluetoothPlatformUtils:
    """Platform-specific Bluetooth utilities."""
    
    @staticmethod
    def get_platform_info() -> Dict[str, Any]:
        """Get platform-specific Bluetooth information."""
        platform = platform.system().lower()
        
        if platform == "windows":
            return BluetoothPlatformUtils._get_windows_info()
        elif platform == "darwin":
            return BluetoothPlatformUtils._get_macos_info()
        elif platform == "linux":
            return BluetoothPlatformUtils._get_linux_info()
        else:
            return {"platform": platform, "supported": False}
    
    @staticmethod
    def _get_windows_info() -> Dict[str, Any]:
        """Get Windows Bluetooth information."""
        try:
            import subprocess
            result = subprocess.run(
                ["powershell", "Get-PnpDevice -Class Bluetooth -Status OK"], 
                capture_output=True, 
                text=True
            )
            
            return {
                "platform": "windows",
                "supported": True,
                "devices": result.stdout if result.returncode == 0 else "Error"
            }
        except Exception:
            return {"platform": "windows", "supported": True, "devices": "Unknown"}
    
    @staticmethod
    def _get_macos_info() -> Dict[str, Any]:
        """Get macOS Bluetooth information."""
        try:
            import subprocess
            result = subprocess.run(
                ["system_profiler", "SPBluetoothDataType"], 
                capture_output=True, 
                text=True
            )
            
            return {
                "platform": "macos",
                "supported": True,
                "info": result.stdout if result.returncode == 0 else "Error"
            }
        except Exception:
            return {"platform": "macos", "supported": True, "info": "Unknown"}
    
    @staticmethod
    def _get_linux_info() -> Dict[str, Any]:
        """Get Linux Bluetooth information."""
        try:
            import subprocess
            result = subprocess.run(
                ["hciconfig"], 
                capture_output=True, 
                text=True
            )
            
            return {
                "platform": "linux",
                "supported": True,
                "adapters": result.stdout if result.returncode == 0 else "Error"
            }
        except Exception:
            return {"platform": "linux", "supported": True, "adapters": "Unknown"}
```

## Testing Strategy

### Unit Tests
- Test platform detection
- Test adapter selection
- Test message parsing
- Test connection management

### Integration Tests
- Test actual Bluetooth connections on each platform
- Test message exchange between devices
- Test reconnection logic

### Platform-Specific Tests
- Windows: Test with Windows 10/11
- macOS: Test with macOS 10.15+
- Linux: Test with Ubuntu, Fedora, Arch

## Error Handling

### Common Errors
- Bluetooth adapter not available
- Device not found
- Connection timeout
- Permission denied

### Platform-Specific Errors
- Windows: Driver issues, service not running
- macOS: Entitlement missing, Bluetooth disabled
- Linux: BlueZ not running, permissions

## Performance Considerations

### Optimization Strategies
- Efficient scanning intervals
- Connection pooling
- Message batching
- Adaptive timeouts

### Resource Management
- Memory usage monitoring
- Connection limits
- Cleanup of disconnected devices

This implementation plan provides comprehensive cross-platform Bluetooth support for the laptop client, ensuring compatibility with Windows, macOS, and Linux systems while maintaining robust error handling and performance optimization.