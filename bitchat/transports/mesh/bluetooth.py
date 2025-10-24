"""
Bluetooth LE Mesh transport implementation for Blue Relay Chat RPi 4 client.

This module provides the Bluetooth Low Energy mesh networking implementation
using the bleak library for cross-platform Bluetooth communication.
"""

import asyncio
import struct
import uuid
from typing import Dict, Any, Optional, List, Set
from datetime import datetime

import bleak
from bleak import BleakScanner, BleakClient
from bleak.backends.device import BLEDevice

from ...config.manager import ConfigManager
from ...utils.logging import get_logger
from ...constants import TransportType, DEFAULT_MESH_TTL
from ...exceptions import BluetoothError, TransportError
from ..base import BaseTransport, TransportStatus
from .mesh_protocol import MeshProtocol
from .discovery import PeerDiscovery
from .routing import MeshRouter


class BluetoothMeshTransport(BaseTransport):
    """Bluetooth LE Mesh transport implementation."""
    
    # Bluetooth service and characteristic UUIDs for BRC
    SERVICE_UUID = uuid.UUID("12345678-1234-1234-1234-123456789abc")
    MESSAGE_CHAR_UUID = uuid.UUID("12345678-1234-1234-1234-123456789abd")
    CONTROL_CHAR_UUID = uuid.UUID("12345678-1234-1234-1234-123456789abe")
    
    def __init__(self, config_manager: ConfigManager) -> None:
        """
        Initialize the Bluetooth mesh transport.
        
        Args:
            config_manager: Configuration manager instance
        """
        super().__init__(config_manager, TransportType.MESH)
        
        # Bluetooth configuration
        self.adapter_name = config_manager.get("bluetooth.adapter_name", "hci0")
        self.scan_interval = config_manager.get("bluetooth.scan_interval_seconds", 10)
        self.advertisement_interval = config_manager.get("bluetooth.advertisement_interval_seconds", 5)
        self.max_peers = config_manager.get("bluetooth.max_peers", 50)
        self.mesh_ttl = config_manager.get("bluetooth.mesh_ttl", DEFAULT_MESH_TTL)
        self.discovery_timeout = config_manager.get("bluetooth.discovery_timeout_seconds", 30)
        self.power_save_mode = config_manager.get("bluetooth.power_save_mode", True)
        
        # Bluetooth components
        self.scanner: Optional[BleakScanner] = None
        self.mesh_protocol = MeshProtocol(config_manager)
        self.peer_discovery = PeerDiscovery(config_manager)
        self.mesh_router = MeshRouter(config_manager)
        
        # Connection state
        self._connected_devices: Dict[str, BleakClient] = {}
        self._device_info: Dict[str, Dict[str, Any]] = {}
        self._scan_task: Optional[asyncio.Task] = None
        self._advertise_task: Optional[asyncio.Task] = None
        
        # Message handling
        self._message_handlers: Dict[str, callable] = {}
        self._pending_messages: Dict[str, asyncio.Future] = {}
    
    async def _do_start(self) -> None:
        """Start the Bluetooth mesh transport."""
        try:
            # Initialize scanner
            self.scanner = BleakScanner(
                adapter=self.adapter_name,
                detection_callback=self._on_device_detected
            )
            
            # Start peer discovery
            await self.peer_discovery.start()
            
            # Start scanning for devices
            await self._start_scanning()
            
            # Start advertising
            await self._start_advertising()
            
            # Set up message handlers
            self._setup_message_handlers()
            
            await self._set_status(TransportStatus.CONNECTED)
            self.logger.info("Bluetooth mesh transport started successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to start Bluetooth mesh transport: {e}")
            raise BluetoothError(f"Bluetooth transport start failed: {e}")
    
    async def _do_stop(self) -> None:
        """Stop the Bluetooth mesh transport."""
        try:
            # Stop advertising
            if self._advertise_task:
                self._advertise_task.cancel()
                try:
                    await self._advertise_task
                except asyncio.CancelledError:
                    pass
                self._advertise_task = None
            
            # Stop scanning
            if self._scan_task:
                self._scan_task.cancel()
                try:
                    await self._scan_task
                except asyncio.CancelledError:
                    pass
                self._scan_task = None
            
            # Disconnect all devices
            for device_id, client in self._connected_devices.items():
                try:
                    if client.is_connected:
                        await client.disconnect()
                except Exception as e:
                    self.logger.error(f"Error disconnecting device {device_id}: {e}")
            
            self._connected_devices.clear()
            self._device_info.clear()
            
            # Stop peer discovery
            await self.peer_discovery.stop()
            
            self.logger.info("Bluetooth mesh transport stopped")
            
        except Exception as e:
            self.logger.error(f"Failed to stop Bluetooth mesh transport: {e}")
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
    
    async def _do_get_connected_peers(self) -> Dict[str, Any]:
        """Get information about connected Bluetooth peers."""
        peers = {}
        
        for device_id, device_info in self._device_info.items():
            peers[device_id] = {
                "id": device_id,
                "name": device_info.get("name", "Unknown"),
                "address": device_info.get("address", ""),
                "rssi": device_info.get("rssi", 0),
                "last_seen": device_info.get("last_seen", datetime.now()).isoformat(),
                "connected": device_id in self._connected_devices,
                "transport_type": "mesh",
            }
        
        return {
            "total_peers": len(peers),
            "connected_peers": len(self._connected_devices),
            "max_peers": self.max_peers,
            "peers": peers,
        }
    
    async def _start_scanning(self) -> None:
        """Start scanning for Bluetooth devices."""
        try:
            self._scan_task = asyncio.create_task(self._scan_loop())
            self.logger.debug("Started Bluetooth scanning")
            
        except Exception as e:
            self.logger.error(f"Failed to start Bluetooth scanning: {e}")
            raise BluetoothError(f"Scanning start failed: {e}")
    
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
    
    async def _start_advertising(self) -> None:
        """Start advertising as a BRC mesh node."""
        try:
            self._advertise_task = asyncio.create_task(self._advertise_loop())
            self.logger.debug("Started Bluetooth advertising")
            
        except Exception as e:
            self.logger.error(f"Failed to start Bluetooth advertising: {e}")
            # Advertising is not critical, so continue without it
    
    async def _advertise_loop(self) -> None:
        """Main advertising loop."""
        while self._running:
            try:
                # In a full implementation, this would set up BLE advertising
                # For now, we'll just simulate it
                await asyncio.sleep(self.advertisement_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in advertise loop: {e}")
                await asyncio.sleep(5)
    
    def _on_device_detected(self, device: BLEakScanner, advertisement_data: bleak.BleakAdvertisementData) -> None:
        """Handle detection of a Bluetooth device."""
        try:
            device_id = device.address
            device_name = device.name or "Unknown"
            
            # Check if this is a BRC device
            if self.SERVICE_UUID in advertisement_data.service_uuids:
                # Update device info
                self._device_info[device_id] = {
                    "name": device_name,
                    "address": device.address,
                    "rssi": advertisement_data.rssi,
                    "last_seen": datetime.now(),
                    "manufacturer_data": advertisement_data.manufacturer_data,
                    "service_data": advertisement_data.service_data,
                }
                
                # Try to connect if we have room
                if (device_id not in self._connected_devices and 
                    len(self._connected_devices) < self.max_peers):
                    asyncio.create_task(self._connect_to_device(device))
                
        except Exception as e:
            self.logger.error(f"Error handling device detection: {e}")
    
    async def _connect_to_device(self, device: BLEDevice) -> None:
        """Connect to a Bluetooth device."""
        try:
            device_id = device.address
            
            # Create client
            client = BleakClient(device, timeout=10)
            
            # Connect
            await client.connect()
            
            # Check if it has the BRC service
            if self.SERVICE_UUID in await client.get_services():
                # Store connected device
                self._connected_devices[device_id] = client
                
                # Set up notification handlers
                await self._setup_notifications(client)
                
                # Exchange mesh information
                await self._exchange_mesh_info(client)
                
                # Notify about peer connection
                await self._on_peer_connected(device_id, self._device_info.get(device_id, {}))
                
                self.logger.info(f"Connected to BRC device: {device.name} ({device_id})")
            else:
                # Not a BRC device, disconnect
                await client.disconnect()
                
        except Exception as e:
            self.logger.error(f"Failed to connect to device {device.address}: {e}")
    
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
            
        except Exception as e:
            self.logger.error(f"Failed to set up notifications: {e}")
    
    async def _exchange_mesh_info(self, client: BleakClient) -> None:
        """Exchange mesh information with a connected device."""
        try:
            # Send our mesh info
            mesh_info = self.mesh_protocol.get_local_mesh_info()
            await client.write_gatt_char(self.CONTROL_CHAR_UUID, mesh_info)
            
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
                # Recipient not connected, route through mesh
                return await self._mesh_router.route_message(message)
                
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
            for client in self._connected_devices.values():
                try:
                    await client.write_gatt_char(self.MESSAGE_CHAR_UUID, mesh_msg)
                    success_count += 1
                except Exception as e:
                    self.logger.error(f"Failed to send channel message to device: {e}")
            
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
            for client in self._connected_devices.values():
                try:
                    await client.write_gatt_char(self.MESSAGE_CHAR_UUID, mesh_msg)
                    success_count += 1
                except Exception as e:
                    self.logger.error(f"Failed to send broadcast message to device: {e}")
            
            return success_count > 0
            
        except Exception as e:
            self.logger.error(f"Failed to send broadcast message: {e}")
            return False
    
    def _setup_message_handlers(self) -> None:
        """Set up message handlers for different message types."""
        self._message_handlers = {
            "text": self._handle_text_message,
            "control": self._handle_control_message,
            "route": self._handle_route_message,
        }
    
    async def _handle_text_message(self, message: Dict[str, Any]) -> None:
        """Handle a text message."""
        await self._on_message_received(message)
    
    async def _handle_route_message(self, message: Dict[str, Any]) -> None:
        """Handle a routing message."""
        await self._mesh_router.handle_route_message(message)
    
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