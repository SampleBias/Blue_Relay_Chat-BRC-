"""
Identity management for Blue Relay Chat RPi 4 client.

This module provides identity and key management functionality
including key generation, storage, and retrieval.
"""

import os
import secrets
from typing import Optional, Dict, Any
from datetime import datetime

from ..config.manager import ConfigManager
from ..utils.logging import get_logger
from ..exceptions import IdentityError
from ..data.models import Identity
from .crypto import CryptoManager


class IdentityManager:
    """Manages user identity and cryptographic keys."""
    
    def __init__(self, config_manager: ConfigManager) -> None:
        """
        Initialize the identity manager.
        
        Args:
            config_manager: Configuration manager instance
        """
        self.config = config_manager
        self.logger = get_logger("identity")
        self.crypto = CryptoManager(config_manager)
        
        # Identity storage path
        self.data_dir = config_manager.get_data_dir()
        self.identity_file = os.path.join(self.data_dir, "identity.json")
        
        # Current identity
        self._identity: Optional[Identity] = None
    
    async def initialize(self) -> None:
        """Initialize the identity manager and load or create identity."""
        try:
            # Ensure data directory exists
            os.makedirs(self.data_dir, exist_ok=True)
            
            # Try to load existing identity
            if await self._load_identity():
                self.logger.info(f"Loaded existing identity: {self._identity.id}")
            else:
                # Create new identity
                await self._create_identity()
                self.logger.info(f"Created new identity: {self._identity.id}")
                
        except Exception as e:
            self.logger.error(f"Failed to initialize identity: {e}")
            raise IdentityError(f"Identity initialization failed: {e}")
    
    async def _load_identity(self) -> bool:
        """
        Load existing identity from storage.
        
        Returns:
            True if identity was loaded successfully, False otherwise
        """
        try:
            if not os.path.exists(self.identity_file):
                return False
            
            # Read identity file
            with open(self.identity_file, 'r') as f:
                import json
                data = json.load(f)
            
            # Decrypt private key if needed
            private_key = data.get("private_key", "")
            if private_key and data.get("encrypted", False):
                # Prompt for password or use environment variable
                password = os.environ.get("BRC_IDENTITY_PASSWORD")
                if not password:
                    # For now, skip encrypted keys
                    # In a full implementation, you would prompt for password
                    self.logger.warning("Encrypted identity found but no password provided")
                    return False
                
                # Decrypt private key
                salt = bytes.fromhex(data["salt"])
                nonce = bytes.fromhex(data["nonce"])
                private_key = self.crypto.decrypt_private_key(
                    bytes.fromhex(private_key),
                    password,
                    salt,
                    nonce
                ).hex()
            
            # Create identity object
            self._identity = Identity(
                id=data["id"],
                public_key=data["public_key"],
                private_key=private_key,
                key_algorithm=data.get("key_algorithm", "ed25519"),
                created_at=datetime.fromisoformat(data["created_at"]),
                last_used=datetime.fromisoformat(data["last_used"]) if data.get("last_used") else None,
                metadata=data.get("metadata", {})
            )
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to load identity: {e}")
            return False
    
    async def _create_identity(self) -> None:
        """Create a new identity."""
        try:
            # Generate new key pair
            private_key, public_key = self.crypto.generate_ed25519_keypair()
            
            # Generate identity ID (hash of public key)
            import hashlib
            identity_id = hashlib.sha256(public_key).hexdigest()[:16]
            
            # Create identity object
            self._identity = Identity(
                id=identity_id,
                public_key=public_key.hex(),
                private_key=private_key.hex(),
                key_algorithm="ed25519",
                created_at=datetime.now(),
                metadata={"created_by": "blue-relay-chat"}
            )
            
            # Save identity
            await self._save_identity()
            
        except Exception as e:
            self.logger.error(f"Failed to create identity: {e}")
            raise IdentityError(f"Identity creation failed: {e}")
    
    async def _save_identity(self) -> None:
        """Save current identity to storage."""
        if not self._identity:
            raise IdentityError("No identity to save")
        
        try:
            # Prepare identity data
            data = {
                "id": self._identity.id,
                "public_key": self._identity.public_key,
                "private_key": self._identity.private_key,
                "key_algorithm": self._identity.key_algorithm,
                "created_at": self._identity.created_at.isoformat(),
                "last_used": self._identity.last_used.isoformat() if self._identity.last_used else None,
                "metadata": self._identity.metadata,
                "encrypted": False  # For now, store unencrypted
            }
            
            # Optionally encrypt private key
            encrypt_keys = self.config.get("security.encrypt_private_keys", False)
            if encrypt_keys:
                password = os.environ.get("BRC_IDENTITY_PASSWORD")
                if password:
                    encrypted_key, salt, nonce = self.crypto.encrypt_private_key(
                        bytes.fromhex(self._identity.private_key),
                        password
                    )
                    data["private_key"] = encrypted_key.hex()
                    data["salt"] = salt.hex()
                    data["nonce"] = nonce.hex()
                    data["encrypted"] = True
            
            # Write to file
            with open(self.identity_file, 'w') as f:
                import json
                json.dump(data, f, indent=2)
            
            # Set secure permissions
            os.chmod(self.identity_file, 0o600)
            
        except Exception as e:
            self.logger.error(f"Failed to save identity: {e}")
            raise IdentityError(f"Identity save failed: {e}")
    
    def get_identity(self) -> Optional[Identity]:
        """
        Get the current identity.
        
        Returns:
            Current identity or None if not initialized
        """
        return self._identity
    
    def get_public_key(self) -> Optional[str]:
        """
        Get the public key of the current identity.
        
        Returns:
            Public key as hex string or None if no identity
        """
        return self._identity.public_key if self._identity else None
    
    def get_private_key(self) -> Optional[str]:
        """
        Get the private key of the current identity.
        
        Returns:
            Private key as hex string or None if no identity
        """
        return self._identity.private_key if self._identity else None
    
    def get_identity_id(self) -> Optional[str]:
        """
        Get the ID of the current identity.
        
        Returns:
            Identity ID or None if no identity
        """
        return self._identity.id if self._identity else None
    
    async def update_last_used(self) -> None:
        """Update the last used timestamp for the current identity."""
        if self._identity:
            self._identity.last_used = datetime.now()
            await self._save_identity()
    
    async def backup_identity(self, backup_path: str, password: Optional[str] = None) -> None:
        """
        Create a backup of the current identity.
        
        Args:
            backup_path: Path to save backup
            password: Optional password for encrypting backup
        """
        if not self._identity:
            raise IdentityError("No identity to backup")
        
        try:
            # Prepare backup data
            data = {
                "id": self._identity.id,
                "public_key": self._identity.public_key,
                "private_key": self._identity.private_key,
                "key_algorithm": self._identity.key_algorithm,
                "created_at": self._identity.created_at.isoformat(),
                "metadata": self._identity.metadata,
                "backup_created_at": datetime.now().isoformat(),
                "encrypted": False
            }
            
            # Encrypt backup if password provided
            if password:
                encrypted_key, salt, nonce = self.crypto.encrypt_private_key(
                    bytes.fromhex(self._identity.private_key),
                    password
                )
                data["private_key"] = encrypted_key.hex()
                data["salt"] = salt.hex()
                data["nonce"] = nonce.hex()
                data["encrypted"] = True
            
            # Write backup
            with open(backup_path, 'w') as f:
                import json
                json.dump(data, f, indent=2)
            
            # Set secure permissions
            os.chmod(backup_path, 0o600)
            
            self.logger.info(f"Identity backed up to {backup_path}")
            
        except Exception as e:
            self.logger.error(f"Failed to backup identity: {e}")
            raise IdentityError(f"Identity backup failed: {e}")
    
    async def restore_identity(self, backup_path: str, password: Optional[str] = None) -> None:
        """
        Restore an identity from a backup.
        
        Args:
            backup_path: Path to backup file
            password: Optional password for decrypting backup
        """
        try:
            # Read backup file
            with open(backup_path, 'r') as f:
                import json
                data = json.load(f)
            
            # Decrypt private key if needed
            private_key = data.get("private_key", "")
            if private_key and data.get("encrypted", False):
                if not password:
                    raise IdentityError("Password required for encrypted backup")
                
                salt = bytes.fromhex(data["salt"])
                nonce = bytes.fromhex(data["nonce"])
                private_key = self.crypto.decrypt_private_key(
                    bytes.fromhex(private_key),
                    password,
                    salt,
                    nonce
                ).hex()
            
            # Create identity object
            self._identity = Identity(
                id=data["id"],
                public_key=data["public_key"],
                private_key=private_key,
                key_algorithm=data.get("key_algorithm", "ed25519"),
                created_at=datetime.fromisoformat(data["created_at"]),
                last_used=None,
                metadata=data.get("metadata", {})
            )
            
            # Save restored identity
            await self._save_identity()
            
            self.logger.info(f"Identity restored from {backup_path}")
            
        except Exception as e:
            self.logger.error(f"Failed to restore identity: {e}")
            raise IdentityError(f"Identity restore failed: {e}")
    
    async def emergency_wipe(self) -> None:
        """Emergency wipe of all identity data."""
        try:
            self.logger.warning("Performing emergency wipe of identity data")
            
            # Clear current identity
            self._identity = None
            
            # Remove identity file
            if os.path.exists(self.identity_file):
                os.remove(self.identity_file)
                self.logger.info("Identity file removed")
            
            # Clear any backup files
            backup_dir = os.path.join(self.data_dir, "backups")
            if os.path.exists(backup_dir):
                import shutil
                shutil.rmtree(backup_dir)
                self.logger.info("Identity backups removed")
            
            self.logger.warning("Emergency wipe completed")
            
        except Exception as e:
            self.logger.error(f"Failed to perform emergency wipe: {e}")
            raise IdentityError(f"Emergency wipe failed: {e}")
    
    def get_identity_info(self) -> Dict[str, Any]:
        """
        Get information about the current identity.
        
        Returns:
            Dictionary containing identity information
        """
        if not self._identity:
            return {"has_identity": False}
        
        return {
            "has_identity": True,
            "id": self._identity.id,
            "public_key": self._identity.public_key,
            "key_algorithm": self._identity.key_algorithm,
            "created_at": self._identity.created_at.isoformat(),
            "last_used": self._identity.last_used.isoformat() if self._identity.last_used else None,
            "identity_file": self.identity_file,
            "encrypted_storage": self.config.get("security.encrypt_private_keys", False),
        }