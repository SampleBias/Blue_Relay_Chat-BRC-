"""
Hardware detection utilities for Blue Relay Chat.

This module provides functionality to detect the current hardware platform
and apply appropriate configuration settings.
"""

import os
import re
from typing import Dict, Any, Optional
from .logging import get_logger


class HardwareProfile:
    """Hardware profile with specific configuration settings."""
    
    def __init__(self, name: str, config_overrides: Dict[str, Any]) -> None:
        self.name = name
        self.config_overrides = config_overrides


class HardwareDetector:
    """Detects hardware platform and provides appropriate configuration."""
    
    def __init__(self) -> None:
        self.logger = get_logger("hardware_detection")
        self._hardware_profiles = self._initialize_profiles()
    
    def _initialize_profiles(self) -> Dict[str, HardwareProfile]:
        """Initialize hardware profiles for supported platforms."""
        return {
            "rpi-zero2w": HardwareProfile(
                "Raspberry Pi Zero 2 W",
                {
                    "bluetooth.max_peers": 15,
                    "bluetooth.scan_interval_seconds": 15,
                    "bluetooth.discovery_timeout_seconds": 45,
                    "bluetooth.mesh_ttl": 5,
                    "nostr.max_relay_connections": 2,
                    "nostr.subscription_limit": 5,
                    "nostr.event_batch_size": 20,
                    "nostr.connection_timeout_seconds": 30,
                    "performance.max_cpu_usage_percent": 60,
                    "performance.max_memory_mb": 150,
                    "performance.message_queue_size": 300,
                    "performance.compression_threshold_bytes": 200,
                    "storage.max_message_history": 5000,
                    "storage.cleanup_interval_hours": 12,
                    "cli.max_display_lines": 500,
                    "cli.refresh_rate_ms": 150,
                    "location.geohash_precision": 4,
                    "location.location_update_interval_minutes": 45,
                    "channels.channel_history_limit": 200,
                    "security.key_derivation_iterations": 75000,
                    "network.connection_timeout_seconds": 45,
                    "network.keepalive_interval_seconds": 90,
                    "network.max_retries": 2,
                    "network.retry_delay_seconds": 10,
                }
            ),
            "rpi-4": HardwareProfile(
                "Raspberry Pi 4",
                {
                    # Default settings for RPi 4 (already in defaults.py)
                }
            ),
            "orangepi-zero2w": HardwareProfile(
                "Orange Pi Zero 2W",
                {
                    "bluetooth.max_peers": 20,
                    "bluetooth.scan_interval_seconds": 12,
                    "bluetooth.discovery_timeout_seconds": 40,
                    "bluetooth.mesh_ttl": 6,
                    "nostr.max_relay_connections": 3,
                    "nostr.subscription_limit": 7,
                    "nostr.event_batch_size": 30,
                    "nostr.connection_timeout_seconds": 25,
                    "performance.max_cpu_usage_percent": 55,
                    "performance.max_memory_mb": 200,
                    "performance.message_queue_size": 500,
                    "performance.compression_threshold_bytes": 150,
                    "storage.max_message_history": 7500,
                    "storage.cleanup_interval_hours": 18,
                    "cli.max_display_lines": 750,
                    "cli.refresh_rate_ms": 120,
                    "location.geohash_precision": 5,
                    "location.location_update_interval_minutes": 35,
                    "channels.channel_history_limit": 350,
                    "security.key_derivation_iterations": 85000,
                    "network.connection_timeout_seconds": 35,
                    "network.keepalive_interval_seconds": 75,
                    "network.max_retries": 3,
                    "network.retry_delay_seconds": 7,
                }
            ),
        }
    
    def detect_hardware(self) -> Optional[str]:
        """
        Detect the current hardware platform.
        
        Returns:
            Hardware identifier string or None if unknown
        """
        # Try device tree first (most reliable for modern ARM boards)
        if os.path.exists("/proc/device-tree/model"):
            try:
                with open("/proc/device-tree/model", "r") as f:
                    model = f.read().strip("\x00")
                    return self._identify_from_model(model)
            except (IOError, OSError) as e:
                self.logger.warning(f"Failed to read device tree model: {e}")
        
        # Try CPU info as fallback
        if os.path.exists("/proc/cpuinfo"):
            try:
                with open("/proc/cpuinfo", "r") as f:
                    cpuinfo = f.read()
                    return self._identify_from_cpuinfo(cpuinfo)
            except (IOError, OSError) as e:
                self.logger.warning(f"Failed to read CPU info: {e}")
        
        # Try DMI information (x86 systems)
        if os.path.exists("/sys/class/dmi/id/product_name"):
            try:
                with open("/sys/class/dmi/id/product_name", "r") as f:
                    product_name = f.read().strip()
                    return self._identify_from_dmi(product_name)
            except (IOError, OSError) as e:
                self.logger.warning(f"Failed to read DMI product name: {e}")
        
        return None
    
    def _identify_from_model(self, model: str) -> Optional[str]:
        """Identify hardware from device tree model string."""
        model_lower = model.lower()
        
        # Raspberry Pi Zero 2 W
        if "raspberry pi zero 2 w" in model_lower:
            return "rpi-zero2w"
        
        # Raspberry Pi 4 variants
        if "raspberry pi 4" in model_lower:
            return "rpi-4"
        
        # Orange Pi Zero 2W
        if "orange pi zero 2w" in model_lower or "orange pi zero 2 w" in model_lower:
            return "orangepi-zero2w"
        
        # Log unknown model for debugging
        self.logger.info(f"Unknown hardware model: {model}")
        return None
    
    def _identify_from_cpuinfo(self, cpuinfo: str) -> Optional[str]:
        """Identify hardware from /proc/cpuinfo."""
        # Look for hardware field
        hw_match = re.search(r'^Hardware\s*:\s*(.+)$', cpuinfo, re.MULTILINE)
        if hw_match:
            hardware = hw_match.group(1).strip().lower()
            
            if "bcm2835" in hardware:  # Raspberry Pi
                # Check revision to distinguish between models
                rev_match = re.search(r'^Revision\s*:\s*(.+)$', cpuinfo, re.MULTILINE)
                if rev_match:
                    revision = rev_match.group(1).strip()
                    if revision.startswith("902120"):  # Pi Zero 2 W
                        return "rpi-zero2w"
                    elif revision.startswith("d03114"):  # Pi 4
                        return "rpi-4"
        
        # Look for model name
        model_match = re.search(r'^Model name\s*:\s*(.+)$', cpuinfo, re.MULTILINE)
        if model_match:
            model_name = model_match.group(1).strip().lower()
            
            if "allwinner h618" in model_name:  # Orange Pi Zero 2W
                return "orangepi-zero2w"
        
        return None
    
    def _identify_from_dmi(self, product_name: str) -> Optional[str]:
        """Identify hardware from DMI product name."""
        product_lower = product_name.lower()
        
        # This would be for x86 systems or other platforms
        # Add more identifications as needed
        
        return None
    
    def get_hardware_profile(self, hardware_id: Optional[str] = None) -> Optional[HardwareProfile]:
        """
        Get hardware profile for detected or specified hardware.
        
        Args:
            hardware_id: Hardware identifier. If None, auto-detects.
            
        Returns:
            HardwareProfile or None if not found
        """
        if hardware_id is None:
            hardware_id = self.detect_hardware()
        
        if hardware_id is None:
            self.logger.warning("Could not detect hardware platform")
            return None
        
        profile = self._hardware_profiles.get(hardware_id)
        if profile:
            self.logger.info(f"Detected hardware: {profile.name}")
        else:
            self.logger.warning(f"Unknown hardware ID: {hardware_id}")
        
        return profile
    
    def get_hardware_info(self) -> Dict[str, Any]:
        """
        Get comprehensive hardware information.
        
        Returns:
            Dictionary with hardware details
        """
        hardware_id = self.detect_hardware()
        profile = self.get_hardware_profile(hardware_id)
        
        info = {
            "detected_hardware": hardware_id,
            "profile_name": profile.name if profile else "Unknown",
            "supported": profile is not None,
        }
        
        # Add system information
        if os.path.exists("/proc/meminfo"):
            try:
                with open("/proc/meminfo", "r") as f:
                    meminfo = f.read()
                    mem_match = re.search(r'^MemTotal:\s*(\d+)\s*kB', meminfo, re.MULTILINE)
                    if mem_match:
                        total_kb = int(mem_match.group(1))
                        info["total_memory_mb"] = total_kb // 1024
            except (IOError, OSError):
                pass
        
        # Add CPU information
        if os.path.exists("/proc/cpuinfo"):
            try:
                with open("/proc/cpuinfo", "r") as f:
                    cpuinfo = f.read()
                    core_count = len(re.findall(r'^processor\s*:', cpuinfo, re.MULTILINE))
                    info["cpu_cores"] = core_count
            except (IOError, OSError):
                pass
        
        return info


# Global hardware detector instance
_hardware_detector = None


def get_hardware_detector() -> HardwareDetector:
    """Get the global hardware detector instance."""
    global _hardware_detector
    if _hardware_detector is None:
        _hardware_detector = HardwareDetector()
    return _hardware_detector


def detect_hardware() -> Optional[str]:
    """Convenience function to detect hardware."""
    detector = get_hardware_detector()
    return detector.detect_hardware()


def get_hardware_profile(hardware_id: Optional[str] = None) -> Optional[HardwareProfile]:
    """Convenience function to get hardware profile."""
    detector = get_hardware_detector()
    return detector.get_hardware_profile(hardware_id)


def get_hardware_info() -> Dict[str, Any]:
    """Convenience function to get hardware information."""
    detector = get_hardware_detector()
    return detector.get_hardware_info()