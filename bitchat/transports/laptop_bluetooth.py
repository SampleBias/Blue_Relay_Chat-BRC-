"""
Laptop Bluetooth transport for Blue Relay Chat client.

This module provides cross-platform Bluetooth communication for laptop devices,
integrating with the existing BRC mesh protocol and security systems.
"""

import asyncio
import platform
import struct
import uuid
from typing import Dict, Any, Optional, List, Set
from datetime import datetime
import subprocess
import os

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
        self.adapter_name = config_manager.get("laptop_bluetooth.adapter_name", "auto")
        self.scan_interval = config_manager.get("laptop_bluetooth.scan_interval_seconds", 30)
        self.max_peers = config_manager.get("laptop_bluetooth.max_peers", 20)
        self.auto_reconnect = config_manager.get("laptop_bluetooth.auto_reconnect", True)
        self.connection_timeout = config_manager.get("laptop_bluetooth.connection_timeout_seconds", 10)
        self.discovery_timeout = config_manager.get("laptop_bluetooth.discovery_timeout_seconds", 30)
        self.power_save_mode = config_manager.get("laptop_bluetooth.power_save_mode", False)
        
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
        
        self.logger.info(f"Laptop Bluetooth transport initialized for {self.platform}")
    
    def _initialize_platform_specific(self) -> None:
        """Initialize platform-specific Bluetooth settings."""
        try:
            if self.platform == "windows":
                self._init_windows_bluetooth()
            elif self.platform == "darwin":  # macOS
                self._init_macos_bluetooth()
            elif self.platform == "linux":
                self._init_linux_bluetooth()
            else:
                self.logger.warning(f"Unsupported platform: {self.platform}")
                
        except Exception as e:
            self.logger.error(f"Platform initialization failed: {e}")
    
    def _init_windows_bluetooth(self) -> None:
        """Initialize Windows-specific Bluetooth settings."""
        self.logger.debug("Initializing Windows Bluetooth")
        # Windows-specific initialization
        # Could check for Windows Bluetooth driver availability
        pass
    
    def _init_macos_bluetooth(self) -> None:
        """Initialize macOS-specific Bluetooth settings."""
        self.logger.debug("Initializing macOS Bluetooth")
        # macOS-specific initialization
        # Could check for macOS Core Bluetooth availability
        pass
    
    def _init_linux_bluetooth(self) -> None:
        """Initialize Linux-specific Bluetooth settings."""
        self.logger.debug("Initializing Linux Bluetooth")
        # Linux-specific initialization
        # Could check for BlueZ availability
        pass
    
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
            result = subprocess.run(
                ["powershell", "Get-PnpDevice -Class Bluetooth -Status OK"],
                capture_output=True,
                text=True,
                timeout=10
            )
            return result.returncode == 0
        except Exception as e:
            self.logger.warning(f"Could not check Windows Bluetooth: {e}")
            return True  # Assume available if we can't check
    
    async def _check_macos_bluetooth(self) -> bool:
        """Check macOS Bluetooth support."""
        try:
            # Check if Bluetooth is available
            result = subprocess.run(
                ["system_profiler", "SPBluetoothDataType"],
                capture_output=True,
                text=True,
                timeout=10
            )
            return "Bluetooth" in result.stdout and "Hardware" in result.stdout
        except Exception as e:
            self.logger.warning(f"Could not check macOS Bluetooth: {e}")
            return True  # Assume available if we can't check
    
    async def _check_linux_bluetooth(self) -> bool:
        """Check Linux Bluetooth support."""
        try:
            # Check if Bluetooth service is running
            result = subprocess.run(
                ["systemctl", "is-active", "bluetooth"],
                capture_output=True,
                text=True,
                timeout=10
            )
            return result.returncode == 0
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
                scanner_kwargs.update(self._get_windows_scanner_params())
            elif self.platform == "darwin":
                scanner_kwargs.update(self._get_macos_scanner_params())
            elif self.platform == "linux":
                scanner_kwargs.update(self._get_linux_scanner_params())
            
            # Get adapter name
            adapter_name = self._get_adapter_name()
            if adapter_name:
                scanner_kwargs["adapter"] = adapter_name
            
            self.scanner = BleakScanner(**scanner_kwargs)
            self.logger.debug(f"Bluetooth scanner initialized for {self.platform}")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize scanner: {e}")
            raise BluetoothError(f"Scanner initialization failed: {e}")
    
    def _get_adapter_name(self) -> Optional[str]:
        """Get the Bluetooth adapter name."""
        if self.adapter_name == "auto":
            # Try to auto-detect adapter
            if self.platform == "linux":
                return self._get_linux_adapter_name()
            elif self.platform == "windows":
                return self._get_windows_adapter_name()
            elif self.platform == "darwin":
                return self._get_macos_adapter_name()
            else:
                return None
        return self.adapter_name
    
    def _get_linux_adapter_name(self) -> Optional[str]:
        """Get Linux Bluetooth adapter name."""
        try:
            result = subprocess.run(
                ["hcitool", "dev"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                for line in lines[1:]:  # Skip header
                    parts = line.split()
                    if len(parts) >= 2:
                        return parts[1]  # Adapter name (hci0, etc.)
            
            return "hci0"  # Default fallback
            
        except Exception as e:
            self.logger.warning(f"Could not get Linux adapter name: {e}")
            return "hci0"  # Default fallback
    
    def _get_windows_adapter_name(self) -> Optional[str]:
        """Get Windows Bluetooth adapter name."""
        # Windows doesn't typically expose adapter names in the same way
        # Return None to let bleak handle it
        return None
    
    def _get_macos_adapter_name(self) -> Optional[str]:
        """Get macOS Bluetooth adapter name."""
        # macOS doesn't typically expose adapter names in the same way
        # Return None to let bleak handle it
        return None
    
    def _get_windows_scanner_params(self) -> Dict[str, Any]:
        """Get Windows-specific scanner parameters."""
        return {
            # Windows-specific parameters
        }
    
    def _get_macos_scanner_params(self) -> Dict[str, Any]:
        """Get macOS-specific scanner parameters."""
        return {
            # macOS-specific parameters
        }
    
    def _get_linux_scanner_params(self) -> Dict[str, Any]:
        """Get Linux-specific scanner parameters."""
        return {
            # Linux-specific parameters
        }
    
    async def _start_discovery(self) -> None:
        """Start the device discovery process."""
        try:
            self._scan_task = asyncio.create_task(self._scan_loop())
            self.logger.debug("Started device discovery")
            
        except Exception as e:
            self.logger.error(f"Failed to start discovery: {e}")
            raise BluetoothError(f"Discovery start failed: {e}")
    
    async def _scan_loop(self) -> None:
        """Main scanning loop."""
        while self._running:
            try:
                # Start scanning
                await self.scanner.start()
                await asyncio.sleep(self.scan_interval)
                await self.scanner.stop()
                
                # Clean up old device entries
                await self._cleanup_old_devices()
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in scan loop: {e}")
                await asyncio.sleep(5)  # Wait before retrying
    
    async def _cleanup_old_devices(self) -> None:
        """Clean up old device entries."""
        try:
            cutoff_time = datetime.now() - timedelta(minutes=5)
            to_remove = []
            
            for device_id, device_info in self._device_info.items():
                if (device_info["last_seen"] < cutoff_time and 
                    device_id not in self._connected_devices):
                    to_remove.append(device_id)
            
            for device_id in to_remove:
                del self._device_info[device_id]
                self.logger.debug(f"Removed old device entry: {device_id}")
                
        except Exception as e:
            self.logger.error(f"Error cleaning up old devices: {e}")
    
    def _on_device_detected(self, device: BLEakScanner, advertisement_data: bleak.BleakAdvertisementData) -> None:
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
                asyncio.create_task(self._on_device_discovered(device_id, self._device_info[device_id]))
                
        except Exception as e:
            self.logger.error(f"Error handling device detection: {e}")
    
    async def _on_device_discovered(self, device_id: str, device_info: Dict[str, Any]) -> None:
        """Handle device discovery notification."""
        try:
            # Publish device discovered event
            await self.event_bus.publish(Event(
                type=EventTypes.BLUETOOTH_DEVICE_DISCOVERED,
                data={"device_id": device_id, "device_info": device_info},
                source="laptop_bluetooth"
            ))
            
        except Exception as e:
            self.logger.error(f"Error handling device discovery: {e}")
    
    async def _connect_to_device(self, device: BLEakClient) -> None:
        """Connect to a Bluetooth device with platform-specific handling."""
        try:
            device_id = device.address
            self.logger.info(f"Connecting to device {device.address}")
            
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
            
            # Connect
            await device.connect(**client_kwargs)
            
            # Check if it has the BRC service
            if self.SERVICE_UUID in await device.get_services():
                # Store connected device
                self._connected_devices[device_id] = device
                
                # Set up notifications
                await self._setup_notifications(device)
                
                # Exchange mesh information
                await self._exchange_mesh_info(device)
                
                # Cancel any reconnect task for this device
                if device_id in self._reconnect_tasks:
                    self._reconnect_tasks[device_id].cancel()
                    del self._reconnect_tasks[device_id]
                
                # Notify about peer connection
                await self._on_peer_connected(device_id, self._device_info.get(device_id, {}))
                
                self.logger.info(f"Connected to BRC device: {device.address}")
            else:
                # Not a BRC device, disconnect
                await device.disconnect()
                self.logger.debug(f"Device {device.address} is not a BRC device, disconnected")
                
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
    
    async def _exchange_mesh_info(self, client: BleakClient) -> None:
        """Exchange mesh information with a connected device."""
        try:
            # Send our mesh info
            mesh_info = self.mesh_protocol.get_local_mesh_info()
            await client.write_gatt_char(self.CONTROL_CHAR_UUID, mesh_info)
            
            self.logger.debug(f"Exchanged mesh info with device {client.address}")
            
        except Exception as e:
            self.logger.error(f"Failed to exchange mesh info: {e}")
    
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
    
    async def _handle_mesh_message(self, message: Dict[str, Any]) -> None:
        """Handle a received mesh message."""
        try:
            # Check if message is for us
            if message.get("recipient_id") == self.mesh_protocol.get_local_id():
                # Message is for us, deliver it
                await self._on_message_received(message)
            else:
                # Message is for someone else, route it
                await self._mesh_router.route_message(message)
            
        except Exception as e:
            self.logger.error(f"Error handling mesh message: {e}")
    
    async def _handle_control_message(self, control_msg: Dict[str, Any]) -> None:
        """Handle a received control message."""
        try:
            msg_type = control_msg.get("type")
            
            if msg_type == "peer_info":
                # Update peer information
                peer_id = control_msg.get("peer_id")
                if peer_id:
                    self.mesh_router.update_peer_info(peer_id, control_msg)
            
            elif msg_type == "route_update":
                # Update routing table
                self.mesh_router.update_routing_table(control_msg)
            
        except Exception as e:
            self.logger.error(f"Error handling control message: {e}")
    
    async def _on_peer_connected(self, device_id: str, device_info: Dict[str, Any]) -> None:
        """Handle peer connection event."""
        try:
            # Publish peer connected event
            await self.event_bus.publish(Event(
                type=EventTypes.PEER_CONNECTED,
                data={
                    "peer_id": device_id,
                    "peer_info": device_info,
                    "transport_type": "mesh"
                },
                source="laptop_bluetooth"
            ))
            
        except Exception as e:
            self.logger.error(f"Error handling peer connected: {e}")
    
    async def _on_message_received(self, message: Dict[str, Any]) -> None:
        """Handle message received event."""
        try:
            # Publish message received event
            await self.event_bus.publish(Event(
                type=EventTypes.MESSAGE_RECEIVED,
                data={"message": message},
                source="laptop_bluetooth"
            ))
            
        except Exception as e:
            self.logger.error(f"Error handling message received: {e}")
    
    def _setup_message_handlers(self) -> None:
        """Set up message handlers for different message types."""
        self._message_handlers = {
            "text": self._handle_text_message,
            "control": self._handle_control_message,
            "route": self._handle_route_message,
        }
    
    async def _handle_text_message(self, message: Dict[str, Any]) -> None:
        """Handle a text message."""
        try:
            # Publish message received event
            await self._on_message_received(message)
            
        except Exception as e:
            self.logger.error(f"Error handling text message: {e}")
    
    async def _handle_route_message(self, message: Dict[str, Any]) -> None:
        """Handle a routing message."""
        try:
            # Handle routing logic
            if hasattr(self, 'mesh_router'):
                await self.mesh_router.handle_route_message(message)
            
        except Exception as e:
            self.logger.error(f"Error handling route message: {e}")
    
    async def _do_stop(self) -> None:
        """Stop the Bluetooth transport."""
        try:
            # Stop scanning
            if self._scan_task:
                self._scan_task.cancel()
                try:
                    await self._scan_task
                except asyncio.CancelledError:
                    pass
                self._scan_task = None
            
            # Stop advertising (if applicable)
            # Note: bleak doesn't support advertising from client side
            
            # Disconnect all devices
            for device_id, client in self._connected_devices.items():
                try:
                    if client.is_connected:
                        await client.disconnect()
                except Exception as e:
                    self.logger.error(f"Error disconnecting device {device_id}: {e}")
            
            self._connected_devices.clear()
            
            # Stop peer discovery
            # Note: This would be implemented in a full version
            
            self.logger.info("Laptop Bluetooth transport stopped")
            
            await self._set_status(TransportStatus.DISCONNECTED)
            
        except Exception as e:
            self.logger.error(f"Failed to stop Bluetooth transport: {e}")
            raise BluetoothError(f"Bluetooth transport stop failed: {e}")
    
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
                
                self.logger.debug(f"Sent direct message to {recipient_id}")
                return True
            else:
                # Recipient not connected
                self.logger.warning(f"Recipient {recipient_id} not connected")
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to send direct message to {recipient_id}: {e}")
            return False
    
    async def _send_channel_message(self, channel_id: str, message: Dict[str, Any]) -> bool:
        """Send a channel message to all peers in the channel."""
        try:
            # Create mesh message
            mesh_msg = self.mesh_protocol.create_channel_message(channel_id, message)
            
            # Send to all connected devices
            success_count = 0
            for device_id, client in self._connected_devices.items():
                try:
                    await client.write_gatt_char(self.MESSAGE_CHAR_UUID, mesh_msg)
                    success_count += 1
                except Exception as e:
                    self.logger.error(f"Failed to send channel message to {device_id}: {e}")
            
            self.logger.debug(f"Sent channel message to {success_count} devices")
            return success_count > 0
            
        except Exception as e:
            self.logger.error(f"Failed to send channel message: {e}")
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
            
            self.logger.debug(f"Sent broadcast message to {success_count} devices")
            return success_count > 0
            
        except Exception as e:
            self.logger.error(f"Failed to send broadcast message: {e}")
            return False
    
    async def _schedule_reconnect(self, device_id: str) -> None:
        """Schedule reconnection to a device."""
        try:
            if device_id in self._reconnect_tasks:
                return  # Already scheduled
            
            async def reconnect_task():
                try:
                    await asyncio.sleep(5)  # Wait before reconnecting
                    
                    # Try to find device again
                    device_info = self._device_info.get(device_id)
                    if device_info:
                        # Create a mock device for reconnection
                        mock_device = BLEakClient(
                            address=device_id,
                            name=device_info.get("name", "Unknown")
                        )
                        
                        # Try to connect
                        await self._connect_to_device(mock_device)
                        
                except asyncio.CancelledError:
                    pass
                except Exception as e:
                    self.logger.error(f"Reconnection failed for {device_id}: {e}")
                finally:
                    if device_id in self._reconnect_tasks:
                        del self._reconnect_tasks[device_id]
            
            self._reconnect_tasks[device_id] = asyncio.create_task(reconnect_task())
            
        except Exception as e:
            self.logger.error(f"Failed to schedule reconnection for {device_id}: {e}")
    
    async def _do_get_connected_peers(self) -> Dict[str, Any]:
        """Get information about connected Bluetooth peers."""
        try:
            peers = {}
            
            for device_id, client in self._connected_devices.items():
                device_info = self._device_info.get(device_id, {})
                
                peers[device_id] = {
                    "id": device_id,
                    "name": device_info.get("name", "Unknown"),
                    "address": device_info.get("address", ""),
                    "rssi": device_info.get("rssi", 0),
                    "last_seen": device_info.get("last_seen", datetime.now()),
                    "connected": True,
                    "transport_type": "mesh",
                    "platform": device_info.get("platform", self.platform)
                }
            
            return {
                "total_peers": len(peers),
                "connected_peers": len(self._connected_devices),
                "max_peers": self.max_peers,
                "peers": peers,
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get connected peers: {e}")
            return {
                "total_peers": 0,
                "connected_peers": 0,
                "max_peers": self.max_peers,
                "peers": {},
                "error": str(e)
            }
    
    def set_mesh_router(self, mesh_router) -> None:
        """Set the mesh router reference."""
        self.mesh_router = mesh_router
    
    def get_platform_info(self) -> Dict[str, Any]:
        """Get platform-specific information."""
        return {
            "platform": self.platform,
            "adapter_name": self._get_adapter_name(),
            "supported": True  # Assume supported if we got this far
        }