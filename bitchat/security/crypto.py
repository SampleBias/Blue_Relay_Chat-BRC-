"""
Cryptographic operations for Blue Relay Chat RPi 4 client.

This module provides cryptographic functions including encryption,
decryption, key generation, and cryptographic utilities.
"""

import os
import secrets
import hashlib
import hmac
from typing import Tuple, Optional, Dict, Any
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.hazmat.backends import default_backend
from cryptography.exceptions import InvalidSignature

from ..config.manager import ConfigManager
from ..utils.logging import get_logger
from ..exceptions import CryptographyError
from ..constants import ENCRYPTION_ALGORITHM, KEY_SIZE, NONCE_SIZE, TAG_SIZE


class CryptoManager:
    """Manages cryptographic operations for the application."""
    
    def __init__(self, config_manager: ConfigManager) -> None:
        """
        Initialize the crypto manager.
        
        Args:
            config_manager: Configuration manager instance
        """
        self.config = config_manager
        self.logger = get_logger("crypto")
        
        # Get encryption settings
        self.algorithm = config_manager.get("security.encryption_algorithm", ENCRYPTION_ALGORITHM)
        self.key_derivation_iterations = config_manager.get("security.key_derivation_iterations", 100000)
        
        # Initialize backend
        self.backend = default_backend()
    
    def generate_key(self) -> bytes:
        """
        Generate a random encryption key.
        
        Returns:
            Random key bytes
        """
        return secrets.token_bytes(KEY_SIZE)
    
    def generate_nonce(self) -> bytes:
        """
        Generate a random nonce for encryption.
        
        Returns:
            Random nonce bytes
        """
        return secrets.token_bytes(NONCE_SIZE)
    
    def derive_key(self, password: str, salt: Optional[bytes] = None) -> Tuple[bytes, bytes]:
        """
        Derive an encryption key from a password using PBKDF2.
        
        Args:
            password: Password to derive key from
            salt: Optional salt bytes, generated if not provided
            
        Returns:
            Tuple of (derived_key, salt)
        """
        if salt is None:
            salt = secrets.token_bytes(16)
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=KEY_SIZE,
            salt=salt,
            iterations=self.key_derivation_iterations,
            backend=self.backend
        )
        
        key = kdf.derive(password.encode())
        return key, salt
    
    def encrypt(self, plaintext: bytes, key: bytes, nonce: Optional[bytes] = None) -> Tuple[bytes, bytes]:
        """
        Encrypt data using the configured algorithm.
        
        Args:
            plaintext: Data to encrypt
            key: Encryption key
            nonce: Optional nonce, generated if not provided
            
        Returns:
            Tuple of (ciphertext, nonce)
        """
        if nonce is None:
            nonce = self.generate_nonce()
        
        try:
            if self.algorithm == "ChaCha20-Poly1305":
                cipher = Cipher(
                    algorithms.ChaCha20(key),
                    modes.Poly1305(nonce),
                    backend=self.backend
                )
                encryptor = cipher.encryptor()
                ciphertext = encryptor.update(plaintext) + encryptor.finalize()
                
                # ChaCha20-Poly1305 includes the tag in the ciphertext
                return ciphertext, nonce
            elif self.algorithm == "AES-256-GCM":
                cipher = Cipher(
                    algorithms.AES(key),
                    modes.GCM(nonce),
                    backend=self.backend
                )
                encryptor = cipher.encryptor()
                ciphertext = encryptor.update(plaintext) + encryptor.finalize()
                
                # GCM mode includes the tag, extract it
                tag = encryptor.tag
                return ciphertext + tag, nonce
            else:
                raise CryptographyError(f"Unsupported encryption algorithm: {self.algorithm}")
                
        except Exception as e:
            raise CryptographyError(f"Encryption failed: {e}")
    
    def decrypt(self, ciphertext: bytes, key: bytes, nonce: bytes) -> bytes:
        """
        Decrypt data using the configured algorithm.
        
        Args:
            ciphertext: Data to decrypt
            key: Encryption key
            nonce: Nonce used for encryption
            
        Returns:
            Decrypted plaintext
        """
        try:
            if self.algorithm == "ChaCha20-Poly1305":
                cipher = Cipher(
                    algorithms.ChaCha20(key),
                    modes.Poly1305(nonce),
                    backend=self.backend
                )
                decryptor = cipher.decryptor()
                plaintext = decryptor.update(ciphertext) + decryptor.finalize()
                return plaintext
                
            elif self.algorithm == "AES-256-GCM":
                # Extract tag from ciphertext (last 16 bytes)
                tag = ciphertext[-TAG_SIZE:]
                actual_ciphertext = ciphertext[:-TAG_SIZE]
                
                cipher = Cipher(
                    algorithms.AES(key),
                    modes.GCM(nonce, tag),
                    backend=self.backend
                )
                decryptor = cipher.decryptor()
                plaintext = decryptor.update(actual_ciphertext) + decryptor.finalize()
                return plaintext
            else:
                raise CryptographyError(f"Unsupported encryption algorithm: {self.algorithm}")
                
        except Exception as e:
            raise CryptographyError(f"Decryption failed: {e}")
    
    def generate_ed25519_keypair(self) -> Tuple[bytes, bytes]:
        """
        Generate an Ed25519 key pair for signing.
        
        Returns:
            Tuple of (private_key, public_key)
        """
        private_key = ed25519.Ed25519PrivateKey.generate()
        public_key = private_key.public_key()
        
        private_bytes = private_key.private_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PrivateFormat.Raw,
            encryption_algorithm=serialization.NoEncryption()
        )
        
        public_bytes = public_key.public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw
        )
        
        return private_bytes, public_bytes
    
    def sign_message(self, message: bytes, private_key: bytes) -> bytes:
        """
        Sign a message using Ed25519 private key.
        
        Args:
            message: Message to sign
            private_key: Ed25519 private key
            
        Returns:
            Signature bytes
        """
        try:
            key = ed25519.Ed25519PrivateKey.from_private_bytes(private_key)
            signature = key.sign(message)
            return signature
        except Exception as e:
            raise CryptographyError(f"Message signing failed: {e}")
    
    def verify_signature(self, message: bytes, signature: bytes, public_key: bytes) -> bool:
        """
        Verify a message signature using Ed25519 public key.
        
        Args:
            message: Original message
            signature: Signature to verify
            public_key: Ed25519 public key
            
        Returns:
            True if signature is valid, False otherwise
        """
        try:
            key = ed25519.Ed25519PublicKey.from_public_bytes(public_key)
            key.verify(signature, message)
            return True
        except InvalidSignature:
            return False
        except Exception as e:
            raise CryptographyError(f"Signature verification failed: {e}")
    
    def compute_hash(self, data: bytes, algorithm: str = "sha256") -> bytes:
        """
        Compute a hash of the given data.
        
        Args:
            data: Data to hash
            algorithm: Hash algorithm (sha256, sha512, etc.)
            
        Returns:
            Hash bytes
        """
        try:
            if algorithm.lower() == "sha256":
                return hashlib.sha256(data).digest()
            elif algorithm.lower() == "sha512":
                return hashlib.sha512(data).digest()
            else:
                raise CryptographyError(f"Unsupported hash algorithm: {algorithm}")
        except Exception as e:
            raise CryptographyError(f"Hash computation failed: {e}")
    
    def compute_hmac(self, data: bytes, key: bytes, algorithm: str = "sha256") -> bytes:
        """
        Compute an HMAC of the given data.
        
        Args:
            data: Data to authenticate
            key: HMAC key
            algorithm: Hash algorithm for HMAC
            
        Returns:
            HMAC bytes
        """
        try:
            if algorithm.lower() == "sha256":
                return hmac.new(key, data, hashlib.sha256).digest()
            elif algorithm.lower() == "sha512":
                return hmac.new(key, data, hashlib.sha512).digest()
            else:
                raise CryptographyError(f"Unsupported HMAC algorithm: {algorithm}")
        except Exception as e:
            raise CryptographyError(f"HMAC computation failed: {e}")
    
    def verify_hmac(self, data: bytes, hmac_value: bytes, key: bytes, algorithm: str = "sha256") -> bool:
        """
        Verify an HMAC of the given data.
        
        Args:
            data: Original data
            hmac_value: HMAC to verify
            key: HMAC key
            algorithm: Hash algorithm used for HMAC
            
        Returns:
            True if HMAC is valid, False otherwise
        """
        try:
            computed_hmac = self.compute_hmac(data, key, algorithm)
            return hmac.compare_digest(computed_hmac, hmac_value)
        except Exception as e:
            raise CryptographyError(f"HMAC verification failed: {e}")
    
    def encrypt_private_key(self, private_key: bytes, password: str) -> Tuple[bytes, bytes, bytes]:
        """
        Encrypt a private key with a password.
        
        Args:
            private_key: Private key bytes to encrypt
            password: Password for encryption
            
        Returns:
            Tuple of (encrypted_key, salt, nonce)
        """
        # Derive key from password
        key, salt = self.derive_key(password)
        
        # Generate nonce
        nonce = self.generate_nonce()
        
        # Encrypt the private key
        encrypted_key, _ = self.encrypt(private_key, key, nonce)
        
        return encrypted_key, salt, nonce
    
    def decrypt_private_key(self, encrypted_key: bytes, password: str, salt: bytes, nonce: bytes) -> bytes:
        """
        Decrypt a private key with a password.
        
        Args:
            encrypted_key: Encrypted private key
            password: Password for decryption
            salt: Salt used for key derivation
            nonce: Nonce used for encryption
            
        Returns:
            Decrypted private key bytes
        """
        # Derive key from password
        key, _ = self.derive_key(password, salt)
        
        # Decrypt the private key
        private_key = self.decrypt(encrypted_key, key, nonce)
        
        return private_key
    
    def generate_key_exchange_keypair(self) -> Tuple[bytes, bytes]:
        """
        Generate a key pair for key exchange (X25519).
        
        Note: This is a placeholder for X25519 implementation.
        In a full implementation, you would use cryptography.hazmat.primitives.asymmetric.x25519
        
        Returns:
            Tuple of (private_key, public_key)
        """
        # For now, use Ed25519 as a placeholder
        # In a full implementation, this should be X25519
        return self.generate_ed25519_keypair()
    
    def compute_shared_secret(self, private_key: bytes, peer_public_key: bytes) -> bytes:
        """
        Compute a shared secret using Diffie-Hellman key exchange.
        
        Note: This is a placeholder for X25519 implementation.
        In a full implementation, you would use cryptography.hazmat.primitives.asymmetric.x25519
        
        Args:
            private_key: Our private key
            peer_public_key: Peer's public key
            
        Returns:
            Shared secret bytes
        """
        # For now, use a simple hash as a placeholder
        # In a full implementation, this should use X25519
        combined = private_key + peer_public_key
        return self.compute_hash(combined)
    
    def get_crypto_info(self) -> Dict[str, Any]:
        """
        Get information about the cryptographic configuration.
        
        Returns:
            Dictionary containing crypto configuration info
        """
        return {
            "encryption_algorithm": self.algorithm,
            "key_size": KEY_SIZE,
            "nonce_size": NONCE_SIZE,
            "tag_size": TAG_SIZE,
            "key_derivation_iterations": self.key_derivation_iterations,
            "supported_algorithms": ["ChaCha20-Poly1305", "AES-256-GCM"],
            "supported_hash_algorithms": ["sha256", "sha512"],
        }