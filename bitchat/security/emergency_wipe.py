"""
Emergency wipe functionality for Blue Relay Chat RPi 4 client.

This module provides emergency data wiping capabilities for
quickly removing all sensitive data from the system.
"""

import os
import shutil
import secrets
import time
from typing import Optional, List
from pathlib import Path

from ..config.manager import ConfigManager
from ..utils.logging import get_logger
from ..exceptions import EmergencyWipeError


class EmergencyWipe:
    """Handles emergency wiping of sensitive data."""
    
    def __init__(self, config_manager: ConfigManager) -> None:
        """
        Initialize the emergency wipe handler.
        
        Args:
            config_manager: Configuration manager instance
        """
        self.config = config_manager
        self.logger = get_logger("emergency_wipe")
        
        # Wipe configuration
        self.confirmations_required = config_manager.get("security.emergency_wipe_confirmations", 3)
        self.gpio_pin = config_manager.get("security.emergency_wipe_gpio", 18)
        self.data_dir = config_manager.get_data_dir()
        
        # GPIO monitoring (if available)
        self._gpio_monitoring = False
        self._gpio_callback = None
    
    def confirm_wipe(self, confirmations: List[str]) -> bool:
        """
        Verify emergency wipe confirmations.
        
        Args:
            confirmations: List of confirmation strings
            
        Returns:
            True if confirmations are valid, False otherwise
        """
        if len(confirmations) != self.confirmations_required:
            return False
        
        # Check if all confirmations match the expected pattern
        expected = ["WIPE"] * self.confirmations_required
        return confirmations == expected
    
    async def perform_emergency_wipe(self, confirmations: Optional[List[str]] = None) -> None:
        """
        Perform emergency wipe of all sensitive data.
        
        Args:
            confirmations: Optional list of confirmation strings
        """
        self.logger.critical("EMERGENCY WIPE INITIATED")
        
        # Verify confirmations if provided
        if confirmations and not self.confirm_wipe(confirmations):
            raise EmergencyWipeError("Invalid confirmations provided")
        
        try:
            # Stop all operations
            await self._stop_operations()
            
            # Wipe identity data
            await self._wipe_identity()
            
            # Wipe database
            await self._wipe_database()
            
            # Wipe configuration
            await self._wipe_configuration()
            
            # Wipe logs
            await self._wipe_logs()
            
            # Wipe temporary files
            await self._wipe_temp_files()
            
            # Secure free space
            await self._secure_free_space()
            
            self.logger.critical("EMERGENCY WIPE COMPLETED")
            
        except Exception as e:
            self.logger.error(f"Emergency wipe failed: {e}")
            raise EmergencyWipeError(f"Emergency wipe failed: {e}")
    
    async def _stop_operations(self) -> None:
        """Stop all running operations."""
        self.logger.info("Stopping all operations")
        
        # This would be implemented to stop all running components
        # For now, just log the action
        await asyncio.sleep(0.1)  # Simulate stopping operations
    
    async def _wipe_identity(self) -> None:
        """Wipe identity data."""
        self.logger.info("Wiping identity data")
        
        identity_file = os.path.join(self.data_dir, "identity.json")
        if os.path.exists(identity_file):
            await self._secure_delete_file(identity_file)
        
        # Wipe any identity backups
        backup_dir = os.path.join(self.data_dir, "backups")
        if os.path.exists(backup_dir):
            await self._secure_delete_directory(backup_dir)
    
    async def _wipe_database(self) -> None:
        """Wipe database files."""
        self.logger.info("Wiping database")
        
        db_file = os.path.join(self.data_dir, "blue-relay-chat.db")
        if os.path.exists(db_file):
            await self._secure_delete_file(db_file)
        
        # Wipe any WAL files
        wal_file = db_file + "-wal"
        shm_file = db_file + "-shm"
        
        if os.path.exists(wal_file):
            await self._secure_delete_file(wal_file)
        
        if os.path.exists(shm_file):
            await self._secure_delete_file(shm_file)
    
    async def _wipe_configuration(self) -> None:
        """Wipe configuration files."""
        self.logger.info("Wiping configuration")
        
        config_files = [
            os.path.join(self.data_dir, "config.ini"),
            os.path.join(self.data_dir, "config.json"),
        ]
        
        for config_file in config_files:
            if os.path.exists(config_file):
                await self._secure_delete_file(config_file)
    
    async def _wipe_logs(self) -> None:
        """Wipe log files."""
        self.logger.info("Wiping logs")
        
        log_dir = os.path.join(self.data_dir, "logs")
        if os.path.exists(log_dir):
            await self._secure_delete_directory(log_dir)
        
        # Wipe system log files if they exist
        system_log_files = [
            os.path.join(self.data_dir, "blue-relay-chat.log"),
            os.path.join(self.data_dir, "blue-relay-chat.log.1"),
            os.path.join(self.data_dir, "blue-relay-chat.log.2"),
        ]
        
        for log_file in system_log_files:
            if os.path.exists(log_file):
                await self._secure_delete_file(log_file)
    
    async def _wipe_temp_files(self) -> None:
        """Wipe temporary files."""
        self.logger.info("Wiping temporary files")
        
        temp_dir = os.path.join(self.data_dir, "temp")
        if os.path.exists(temp_dir):
            await self._secure_delete_directory(temp_dir)
        
        # Wipe any other temp files
        temp_patterns = [
            "*.tmp",
            "*.temp",
            "*.cache",
            "*.swap",
        ]
        
        for pattern in temp_patterns:
            import glob
            temp_files = glob.glob(os.path.join(self.data_dir, pattern))
            for temp_file in temp_files:
                if os.path.exists(temp_file):
                    await self._secure_delete_file(temp_file)
    
    async def _secure_delete_file(self, file_path: str, passes: int = 3) -> None:
        """
        Securely delete a file by overwriting it multiple times.
        
        Args:
            file_path: Path to file to delete
            passes: Number of overwrite passes
        """
        try:
            if not os.path.exists(file_path):
                return
            
            file_size = os.path.getsize(file_path)
            
            # Overwrite file multiple times
            for pass_num in range(passes):
                with open(file_path, 'r+b') as f:
                    if pass_num == 0:
                        # Pass 1: Write zeros
                        pattern = b'\x00'
                    elif pass_num == 1:
                        # Pass 2: Write ones
                        pattern = b'\xFF'
                    else:
                        # Pass 3+: Write random data
                        pattern = secrets.token_bytes(1)
                    
                    # Write pattern to file
                    remaining = file_size
                    while remaining > 0:
                        chunk_size = min(4096, remaining)
                        chunk = pattern * chunk_size
                        f.write(chunk)
                        remaining -= chunk_size
                    
                    f.flush()
                    os.fsync(f.fileno())
            
            # Remove the file
            os.remove(file_path)
            
        except Exception as e:
            self.logger.error(f"Failed to securely delete file {file_path}: {e}")
            # Try to remove the file anyway
            try:
                os.remove(file_path)
            except:
                pass
    
    async def _secure_delete_directory(self, dir_path: str) -> None:
        """
        Securely delete a directory and all its contents.
        
        Args:
            dir_path: Path to directory to delete
        """
        try:
            if not os.path.exists(dir_path):
                return
            
            # Delete all files in directory
            for root, dirs, files in os.walk(dir_path, topdown=False):
                for file in files:
                    file_path = os.path.join(root, file)
                    await self._secure_delete_file(file_path)
                
                for dir_name in dirs:
                    dir_path_to_delete = os.path.join(root, dir_name)
                    try:
                        os.rmdir(dir_path_to_delete)
                    except:
                        pass
            
            # Remove the directory itself
            os.rmdir(dir_path)
            
        except Exception as e:
            self.logger.error(f"Failed to securely delete directory {dir_path}: {e}")
            # Try to remove the directory anyway
            try:
                shutil.rmtree(dir_path)
            except:
                pass
    
    async def _secure_free_space(self) -> None:
        """Securely wipe free space in the data directory."""
        self.logger.info("Securing free space")
        
        try:
            # Create a large temporary file to fill free space
            temp_file = os.path.join(self.data_dir, f"wipe_{int(time.time())}.tmp")
            
            try:
                # Write random data until we run out of space
                with open(temp_file, 'wb') as f:
                    chunk_size = 1024 * 1024  # 1MB chunks
                    while True:
                        chunk = secrets.token_bytes(chunk_size)
                        f.write(chunk)
                        f.flush()
                        os.fsync(f.fileno())
                        
            except (OSError, IOError):
                # Expected when we run out of space
                pass
            
            # Securely delete the temporary file
            if os.path.exists(temp_file):
                await self._secure_delete_file(temp_file)
                
        except Exception as e:
            self.logger.error(f"Failed to secure free space: {e}")
    
    def setup_gpio_monitoring(self, callback) -> bool:
        """
        Set up GPIO monitoring for emergency wipe trigger.
        
        Args:
            callback: Function to call when GPIO is triggered
            
        Returns:
            True if monitoring was set up successfully, False otherwise
        """
        try:
            # Try to import GPIO library
            import RPi.GPIO as GPIO
            
            # Set up GPIO
            GPIO.setmode(GPIO.BCM)
            GPIO.setup(self.gpio_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
            
            # Set up callback
            def gpio_callback(channel):
                self.logger.critical(f"Emergency wipe GPIO triggered on pin {channel}")
                callback()
            
            GPIO.add_event_detect(
                self.gpio_pin,
                GPIO.FALLING,
                callback=gpio_callback,
                bouncetime=1000
            )
            
            self._gpio_monitoring = True
            self._gpio_callback = gpio_callback
            
            self.logger.info(f"GPIO monitoring set up on pin {self.gpio_pin}")
            return True
            
        except ImportError:
            self.logger.warning("RPi.GPIO library not available, GPIO monitoring disabled")
            return False
        except Exception as e:
            self.logger.error(f"Failed to set up GPIO monitoring: {e}")
            return False
    
    def stop_gpio_monitoring(self) -> None:
        """Stop GPIO monitoring."""
        if self._gpio_monitoring:
            try:
                import RPi.GPIO as GPIO
                GPIO.remove_event_detect(self.gpio_pin)
                GPIO.cleanup()
                self._gpio_monitoring = False
                self.logger.info("GPIO monitoring stopped")
            except Exception as e:
                self.logger.error(f"Failed to stop GPIO monitoring: {e}")
    
    def get_wipe_status(self) -> dict:
        """
        Get the current status of the emergency wipe system.
        
        Returns:
            Dictionary containing wipe system status
        """
        return {
            "confirmations_required": self.confirmations_required,
            "gpio_pin": self.gpio_pin,
            "gpio_monitoring_active": self._gpio_monitoring,
            "data_directory": self.data_dir,
            "data_exists": os.path.exists(self.data_dir),
        }
    
    async def test_wipe_procedure(self, dry_run: bool = True) -> dict:
        """
        Test the emergency wipe procedure without actually wiping data.
        
        Args:
            dry_run: If True, don't actually delete files
            
        Returns:
            Dictionary containing test results
        """
        self.logger.info(f"Running emergency wipe test (dry_run={dry_run})")
        
        results = {
            "identity_files": [],
            "database_files": [],
            "config_files": [],
            "log_files": [],
            "temp_files": [],
            "total_files": 0,
        }
        
        # Check for identity files
        identity_file = os.path.join(self.data_dir, "identity.json")
        if os.path.exists(identity_file):
            results["identity_files"].append(identity_file)
        
        # Check for database files
        db_file = os.path.join(self.data_dir, "blue-relay-chat.db")
        if os.path.exists(db_file):
            results["database_files"].append(db_file)
        
        # Check for other files
        for root, dirs, files in os.walk(self.data_dir):
            for file in files:
                file_path = os.path.join(root, file)
                if file_path.endswith(".log"):
                    results["log_files"].append(file_path)
                elif file.endswith((".tmp", ".temp", ".cache", ".swap")):
                    results["temp_files"].append(file_path)
                elif file.endswith((".ini", ".json")) and "config" in file:
                    results["config_files"].append(file_path)
        
        # Calculate total
        results["total_files"] = (
            len(results["identity_files"]) +
            len(results["database_files"]) +
            len(results["config_files"]) +
            len(results["log_files"]) +
            len(results["temp_files"])
        )
        
        # Perform actual wipe if not dry run
        if not dry_run and results["total_files"] > 0:
            await self.perform_emergency_wipe()
        
        self.logger.info(f"Wipe test completed: {results['total_files']} files found")
        return results