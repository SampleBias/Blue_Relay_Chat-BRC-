"""
Noise Protocol implementation for Blue Relay Chat RPi 4 client.

This module provides Noise Protocol framework implementation for
secure key exchange and encrypted communication in the mesh network.
"""

import secrets
import struct
from typing import Tuple, Optional, Dict, Any
from enum import Enum

from ..config.manager import ConfigManager
from ..utils.logging import get_logger
from ..exceptions import CryptographyError
from .crypto import CryptoManager


class NoisePattern(Enum):
    """Supported Noise Protocol patterns."""
    XX = "XX"  # Mutual authentication with static keys


class NoiseProtocolHandler:
    """
    Handles Noise Protocol operations for secure mesh communication.
    
    Implements the XX pattern for mutual authentication with static keys.
    """
    
    def __init__(self, config_manager: ConfigManager) -> None:
        """
        Initialize the Noise Protocol handler.
        
        Args:
            config_manager: Configuration manager instance
        """
        self.config = config_manager
        self.logger = get_logger("noise_protocol")
        self.crypto = CryptoManager(config_manager)
        
        # Protocol configuration
        self.pattern = NoisePattern.XX
        self.cipher_suite = "ChaCha20-Poly1305"
        self.hash_function = "SHA256"
        
        # Handshake state
        self._handshake_state: Optional[Dict[str, Any]] = None
    
    def initialize_handshake(
        self,
        local_static_keypair: Tuple[bytes, bytes],
        is_initiator: bool = True,
        remote_static_public_key: Optional[bytes] = None
    ) -> Dict[str, Any]:
        """
        Initialize a new handshake session.
        
        Args:
            local_static_keypair: Tuple of (private_key, public_key)
            is_initiator: Whether this side is the initiator
            remote_static_public_key: Remote peer's static public key (if known)
            
        Returns:
            Handshake state dictionary
        """
        try:
            # Generate ephemeral key pair for this handshake
            local_ephemeral_keypair = self.crypto.generate_ed25519_keypair()
            
            # Initialize handshake state
            handshake_state = {
                "pattern": self.pattern,
                "is_initiator": is_initiator,
                "local_static": {
                    "private_key": local_static_keypair[0],
                    "public_key": local_static_keypair[1],
                },
                "local_ephemeral": {
                    "private_key": local_ephemeral_keypair[0],
                    "public_key": local_ephemeral_keypair[1],
                },
                "remote_static": {
                    "public_key": remote_static_public_key,
                },
                "remote_ephemeral": {
                    "public_key": None,
                },
                "handshake_hash": None,
                "ck": None,  # Chaining key
                "h": None,   # Handshake hash
                "session_keys": None,
                "completed": False,
            }
            
            # Initialize protocol state
            self._initialize_protocol_state(handshake_state)
            
            self._handshake_state = handshake_state
            self.logger.debug(f"Initialized {self.pattern.value} handshake (initiator: {is_initiator})")
            
            return handshake_state
            
        except Exception as e:
            raise CryptographyError(f"Handshake initialization failed: {e}")
    
    def _initialize_protocol_state(self, handshake_state: Dict[str, Any]) -> None:
        """Initialize the cryptographic state for the handshake."""
        # Protocol name for mixing
        protocol_name = f"Noise_{self.pattern.value}_{self.cipher_suite}_{self.hash_function}"
        
        # Initialize chaining key and handshake hash
        handshake_state["ck"] = self.crypto.compute_hash(protocol_name.encode())
        handshake_state["h"] = handshake_state["ck"]
        
        # Mix prologue if needed (for XX pattern, no prologue)
        # handshake_state["h"] = self.crypto.compute_hash(handshake_state["h"] + prologue)
    
    def write_message(self, payload: bytes = b"") -> Tuple[bytes, Dict[str, Any]]:
        """
        Write a handshake message.
        
        Args:
            payload: Optional payload to include in the message
            
        Returns:
            Tuple of (message_bytes, updated_handshake_state)
        """
        if not self._handshake_state:
            raise CryptographyError("Handshake not initialized")
        
        if not self._handshake_state["is_initiator"]:
            raise CryptographyError("Only initiator can write messages in current state")
        
        handshake_state = self._handshake_state
        
        try:
            if handshake_state["pattern"] == NoisePattern.XX:
                if handshake_state["remote_ephemeral"]["public_key"] is None:
                    # -> e, es
                    message = self._write_xx_1(handshake_state, payload)
                else:
                    # -> se
                    message = self._write_xx_3(handshake_state, payload)
            else:
                raise CryptographyError(f"Unsupported pattern: {handshake_state['pattern']}")
            
            return message
            
        except Exception as e:
            raise CryptographyError(f"Failed to write handshake message: {e}")
    
    def read_message(self, message: bytes) -> Tuple[Optional[bytes], Dict[str, Any]]:
        """
        Read a handshake message.
        
        Args:
            message: Received handshake message
            
        Returns:
            Tuple of (payload_bytes, updated_handshake_state)
        """
        if not self._handshake_state:
            raise CryptographyError("Handshake not initialized")
        
        if self._handshake_state["is_initiator"]:
            raise CryptographyError("Only responder can read messages in current state")
        
        handshake_state = self._handshake_state
        
        try:
            if handshake_state["pattern"] == NoisePattern.XX:
                if handshake_state["remote_ephemeral"]["public_key"] is None:
                    # <- e, ee
                    payload = self._read_xx_2(handshake_state, message)
                else:
                    # <- se
                    payload = self._read_xx_4(handshake_state, message)
            else:
                raise CryptographyError(f"Unsupported pattern: {handshake_state['pattern']}")
            
            return payload, handshake_state
            
        except Exception as e:
            raise CryptographyError(f"Failed to read handshake message: {e}")
    
    def _write_xx_1(self, handshake_state: Dict[str, Any], payload: bytes) -> bytes:
        """Write XX pattern message 1: -> e, es"""
        # Get local ephemeral public key
        local_ephemeral_pub = handshake_state["local_ephemeral"]["public_key"]
        
        # Mix e into handshake hash
        handshake_state["h"] = self.crypto.compute_hash(
            handshake_state["h"] + struct.pack("!B", len(local_ephemeral_pub)) + local_ephemeral_pub
        )
        
        # Perform DH to get shared secret
        if handshake_state["remote_static"]["public_key"]:
            shared_secret = self.crypto.compute_shared_secret(
                handshake_state["local_ephemeral"]["private_key"],
                handshake_state["remote_static"]["public_key"]
            )
            
            # Derive new chaining keys
            handshake_state["ck"], k = self._derive_keys(handshake_state["ck"], shared_secret)
            
            # Encrypt and authenticate payload
            if payload:
                nonce = self.crypto.generate_nonce()
                ciphertext, _ = self.crypto.encrypt(payload, k, nonce)
                message = local_ephemeral_pub + nonce + ciphertext
            else:
                message = local_ephemeral_pub
        else:
            message = local_ephemeral_pub
        
        return message
    
    def _read_xx_2(self, handshake_state: Dict[str, Any], message: bytes) -> Optional[bytes]:
        """Read XX pattern message 2: <- e, ee"""
        # Parse message
        if len(message) < 32:  # Ed25519 public key size
            raise CryptographyError("Invalid message length")
        
        remote_ephemeral_pub = message[:32]
        handshake_state["remote_ephemeral"]["public_key"] = remote_ephemeral_pub
        
        # Mix e into handshake hash
        handshake_state["h"] = self.crypto.compute_hash(
            handshake_state["h"] + struct.pack("!B", len(remote_ephemeral_pub)) + remote_ephemeral_pub
        )
        
        # Perform DH operations
        shared_secret = self.crypto.compute_shared_secret(
            handshake_state["local_ephemeral"]["private_key"],
            remote_ephemeral_pub
        )
        
        # Derive new chaining keys
        handshake_state["ck"], k = self._derive_keys(handshake_state["ck"], shared_secret)
        
        # Decrypt payload if present
        if len(message) > 32:
            nonce = message[32:44]  # 12-byte nonce
            ciphertext = message[44:]
            payload = self.crypto.decrypt(ciphertext, k, nonce)
            return payload
        
        return None
    
    def _write_xx_3(self, handshake_state: Dict[str, Any], payload: bytes) -> bytes:
        """Write XX pattern message 3: -> se"""
        # Perform DH
        shared_secret = self.crypto.compute_shared_secret(
            handshake_state["local_static"]["private_key"],
            handshake_state["remote_ephemeral"]["public_key"]
        )
        
        # Derive new chaining keys
        handshake_state["ck"], k = self._derive_keys(handshake_state["ck"], shared_secret)
        
        # Mix static public key into handshake hash
        local_static_pub = handshake_state["local_static"]["public_key"]
        handshake_state["h"] = self.crypto.compute_hash(
            handshake_state["h"] + struct.pack("!B", len(local_static_pub)) + local_static_pub
        )
        
        # Encrypt payload
        nonce = self.crypto.generate_nonce()
        ciphertext, _ = self.crypto.encrypt(payload, k, nonce)
        
        message = nonce + ciphertext
        return message
    
    def _read_xx_4(self, handshake_state: Dict[str, Any], message: bytes) -> Optional[bytes]:
        """Read XX pattern message 4: <- se"""
        # Parse message
        if len(message) < 12:  # Minimum nonce size
            raise CryptographyError("Invalid message length")
        
        nonce = message[:12]
        ciphertext = message[12:]
        
        # Perform DH
        shared_secret = self.crypto.compute_shared_secret(
            handshake_state["local_static"]["private_key"],
            handshake_state["remote_ephemeral"]["public_key"]
        )
        
        # Derive new chaining keys
        handshake_state["ck"], k = self._derive_keys(handshake_state["ck"], shared_secret)
        
        # Decrypt payload
        payload = self.crypto.decrypt(ciphertext, k, nonce)
        
        # Mark handshake as complete and derive session keys
        handshake_state["completed"] = True
        handshake_state["session_keys"] = self._derive_session_keys(handshake_state["ck"])
        
        return payload
    
    def _derive_keys(self, ck: bytes, input_key_material: bytes) -> Tuple[bytes, bytes]:
        """
        Derive new chaining key and encryption key using HKDF.
        
        Args:
            ck: Current chaining key
            input_key_material: Input key material from DH operation
            
        Returns:
            Tuple of (new_chaining_key, encryption_key)
        """
        # Simplified HKDF-like derivation
        # In a full implementation, you would use proper HKDF
        temp_key = self.crypto.compute_hmac(ck, input_key_material)
        new_ck = self.crypto.compute_hmac(temp_key, b"\x01")
        k = self.crypto.compute_hmac(temp_key, b"\x02")
        
        return new_ck, k
    
    def _derive_session_keys(self, ck: bytes) -> Dict[str, bytes]:
        """
        Derive session keys for encrypted communication.
        
        Args:
            ck: Final chaining key
            
        Returns:
            Dictionary containing encryption and decryption keys
        """
        # Derive keys using HKDF-like approach
        temp_key = self.crypto.compute_hmac(ck, b"session_keys")
        
        encrypt_key = self.crypto.compute_hmac(temp_key, b"encrypt")
        decrypt_key = self.crypto.compute_hmac(temp_key, b"decrypt")
        
        return {
            "encrypt_key": encrypt_key,
            "decrypt_key": decrypt_key,
        }
    
    def encrypt_message(self, plaintext: bytes, associated_data: bytes = b"") -> bytes:
        """
        Encrypt a message using session keys.
        
        Args:
            plaintext: Message to encrypt
            associated_data: Additional authenticated data
            
        Returns:
            Encrypted message with nonce and tag
        """
        if not self._handshake_state or not self._handshake_state["completed"]:
            raise CryptographyError("Handshake not completed")
        
        session_keys = self._handshake_state["session_keys"]
        encrypt_key = session_keys["encrypt_key"]
        
        # Generate nonce
        nonce = self.crypto.generate_nonce()
        
        # Encrypt message
        ciphertext, _ = self.crypto.encrypt(plaintext, encrypt_key, nonce)
        
        # Return nonce + ciphertext
        return nonce + ciphertext
    
    def decrypt_message(self, ciphertext: bytes, associated_data: bytes = b"") -> bytes:
        """
        Decrypt a message using session keys.
        
        Args:
            ciphertext: Encrypted message with nonce
            associated_data: Additional authenticated data
            
        Returns:
            Decrypted plaintext
        """
        if not self._handshake_state or not self._handshake_state["completed"]:
            raise CryptographyError("Handshake not completed")
        
        if len(ciphertext) < 12:  # Minimum nonce size
            raise CryptographyError("Invalid ciphertext length")
        
        session_keys = self._handshake_state["session_keys"]
        decrypt_key = session_keys["decrypt_key"]
        
        # Extract nonce and ciphertext
        nonce = ciphertext[:12]
        actual_ciphertext = ciphertext[12:]
        
        # Decrypt message
        plaintext = self.crypto.decrypt(actual_ciphertext, decrypt_key, nonce)
        
        return plaintext
    
    def get_handshake_info(self) -> Dict[str, Any]:
        """
        Get information about the current handshake state.
        
        Returns:
            Dictionary containing handshake information
        """
        if not self._handshake_state:
            return {"handshake_active": False}
        
        return {
            "handshake_active": True,
            "pattern": self._handshake_state["pattern"].value,
            "is_initiator": self._handshake_state["is_initiator"],
            "completed": self._handshake_state["completed"],
            "has_remote_static": self._handshake_state["remote_static"]["public_key"] is not None,
            "has_remote_ephemeral": self._handshake_state["remote_ephemeral"]["public_key"] is not None,
            "cipher_suite": self.cipher_suite,
            "hash_function": self.hash_function,
        }
    
    def reset_handshake(self) -> None:
        """Reset the current handshake state."""
        self._handshake_state = None
        self.logger.debug("Handshake state reset")