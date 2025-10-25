"""
Database service for Blue Relay Chat laptop client.

This module provides a simple database service using standard SQLite
without requiring additional dependencies.
"""

import asyncio
import sqlite3
import os
from typing import Dict, Any, Optional, List
from datetime import datetime

from ..config.manager import ConfigManager
from ..utils.logging import get_logger


class DatabaseService:
    """Simple database service using SQLite."""
    
    def __init__(self, config_manager: ConfigManager) -> None:
        """
        Initialize the database service.
        
        Args:
            config_manager: Configuration manager instance
        """
        self.config = config_manager
        self.logger = get_logger("database")
        
        # Database connection
        self.connection: Optional[sqlite3.Connection] = None
        
        # Database configuration
        self.db_path = self._get_database_path()
        
        self.logger.info(f"Database service initialized with path: {self.db_path}")
    
    def _get_database_path(self) -> str:
        """Get the database file path."""
        data_dir = self.config.get_data_dir()
        db_file = self.config.get("storage.database_file", "laptop_client.db")
        return os.path.join(data_dir, db_file)
    
    async def initialize(self) -> None:
        """Initialize the database service."""
        try:
            # Create data directory if it doesn't exist
            os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
            
            # Connect to database
            self.connection = sqlite3.connect(self.db_path)
            self.connection.row_factory = sqlite3.Row
            
            # Create tables if they don't exist
            await self._create_tables()
            
            self.logger.info(f"Database initialized: {self.db_path}")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize database: {e}")
            raise
    
    async def _create_tables(self) -> None:
        """Create database tables if they don't exist."""
        if not self.connection:
            return
        
        try:
            # Create messages table
            await self._execute_query("""
                CREATE TABLE IF NOT EXISTS messages (
                    id TEXT PRIMARY KEY,
                    sender_id TEXT NOT NULL,
                    recipient_id TEXT,
                    channel_id TEXT,
                    content TEXT NOT NULL,
                    message_type TEXT DEFAULT 'text',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    received_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    transport_type TEXT,
                    platform TEXT,
                    encrypted BOOLEAN DEFAULT 0
                )
            """)
            
            # Create peers table
            await self._execute_query("""
                CREATE TABLE IF NOT EXISTS peers (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    address TEXT NOT NULL,
                    status TEXT DEFAULT 'offline',
                    last_seen TIMESTAMP,
                    trust_level INTEGER DEFAULT 0,
                    platform TEXT,
                    first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create channels table
            await self._execute_query("""
                CREATE TABLE IF NOT EXISTS channels (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    type TEXT DEFAULT 'mesh',
                    is_private BOOLEAN DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    description TEXT
                )
            """)
            
            # Create settings table
            await self._execute_query("""
                CREATE TABLE IF NOT EXISTS settings (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            self.logger.debug("Database tables created/verified")
            
        except Exception as e:
            self.logger.error(f"Failed to create tables: {e}")
            raise
    
    async def _execute_query(self, query: str, params: tuple = ()) -> None:
        """Execute a database query."""
        if not self.connection:
            return None
        
        try:
            cursor = self.connection.cursor()
            cursor.execute(query, params)
            self.connection.commit()
            return cursor
        except Exception as e:
            self.logger.error(f"Failed to execute query: {e}")
            raise
    
    async def save_message(self, message: Dict[str, Any]) -> None:
        """
        Save a message to the database.
        
        Args:
            message: Message dictionary containing all fields
        """
        try:
            await self._execute_query("""
                INSERT OR REPLACE INTO messages 
                (id, sender_id, recipient_id, channel_id, content, 
                 message_type, created_at, received_at, transport_type, platform, encrypted)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                message.get("id", self._generate_message_id()),
                message.get("sender_id"),
                message.get("recipient_id"),
                message.get("channel_id"),
                message.get("content"),
                message.get("type", "text"),
                message.get("timestamp", datetime.now()),
                message.get("received_at", datetime.now()),
                message.get("transport_type", "mesh"),
                message.get("platform", ""),
                message.get("encrypted", False)
            ))
            
            self.logger.debug(f"Saved message: {message.get('id', 'unknown')}")
            
        except Exception as e:
            self.logger.error(f"Failed to save message: {e}")
    
    async def get_messages(self, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """
        Get messages from the database.
        
        Args:
            limit: Maximum number of messages to return
            offset: Number of messages to skip
            
        Returns:
            List of message dictionaries
        """
        try:
            cursor = await self._execute_query("""
                SELECT id, sender_id, recipient_id, channel_id, content, 
                       message_type, created_at, received_at, transport_type, platform, encrypted
                FROM messages 
                ORDER BY created_at DESC 
                LIMIT ? OFFSET ?
            """, (limit, offset))
            
            messages = []
            for row in cursor.fetchall():
                messages.append({
                    "id": row[0],
                    "sender_id": row[1],
                    "recipient_id": row[2],
                    "channel_id": row[3],
                    "content": row[4],
                    "type": row[5],
                    "created_at": row[6],
                    "received_at": row[7],
                    "transport_type": row[8],
                    "platform": row[9],
                    "encrypted": bool(row[10])
                })
            
            self.logger.debug(f"Retrieved {len(messages)} messages")
            return messages
            
        except Exception as e:
            self.logger.error(f"Failed to get messages: {e}")
            return []
    
    async def save_peer(self, peer: Dict[str, Any]) -> None:
        """
        Save or update a peer in the database.
        
        Args:
            peer: Peer dictionary containing all fields
        """
        try:
            await self._execute_query("""
                INSERT OR REPLACE INTO peers 
                (id, name, address, status, last_seen, trust_level, platform, first_seen)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                peer.get("id"),
                peer.get("name"),
                peer.get("address"),
                peer.get("status", "offline"),
                peer.get("last_seen", datetime.now()),
                peer.get("trust_level", 0),
                peer.get("platform", ""),
                peer.get("first_seen", datetime.now())
            ))
            
            self.logger.debug(f"Saved peer: {peer.get('id', 'unknown')}")
            
        except Exception as e:
            self.logger.error(f"Failed to save peer: {e}")
    
    async def get_peers(self) -> List[Dict[str, Any]]:
        """
        Get all peers from the database.
        
        Returns:
            List of peer dictionaries
        """
        try:
            cursor = await self._execute_query("""
                SELECT id, name, address, status, last_seen, trust_level, platform, first_seen
                FROM peers
                ORDER BY last_seen DESC
            """)
            
            peers = []
            for row in cursor.fetchall():
                peers.append({
                    "id": row[0],
                    "name": row[1],
                    "address": row[2],
                    "status": row[3],
                    "last_seen": row[4],
                    "trust_level": row[5],
                    "platform": row[6],
                    "first_seen": row[7]
                })
            
            self.logger.debug(f"Retrieved {len(peers)} peers")
            return peers
            
        except Exception as e:
            self.logger.error(f"Failed to get peers: {e}")
            return []
    
    async def save_channel(self, channel: Dict[str, Any]) -> None:
        """
        Save or update a channel in the database.
        
        Args:
            channel: Channel dictionary containing all fields
        """
        try:
            await self._execute_query("""
                INSERT OR REPLACE INTO channels 
                (id, name, type, is_private, created_at, description)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                channel.get("id"),
                channel.get("name"),
                channel.get("type", "mesh"),
                channel.get("is_private", False),
                channel.get("created_at", datetime.now()),
                channel.get("description", "")
            ))
            
            self.logger.debug(f"Saved channel: {channel.get('id', 'unknown')}")
            
        except Exception as e:
            self.logger.error(f"Failed to save channel: {e}")
    
    async def get_channels(self) -> List[Dict[str, Any]]:
        """
        Get all channels from the database.
        
        Returns:
            List of channel dictionaries
        """
        try:
            cursor = await self._execute_query("""
                SELECT id, name, type, is_private, created_at, description
                FROM channels
                ORDER BY created_at DESC
            """)
            
            channels = []
            for row in cursor.fetchall():
                channels.append({
                    "id": row[0],
                    "name": row[1],
                    "type": row[2],
                    "is_private": bool(row[3]),
                    "created_at": row[4],
                    "description": row[5]
                })
            
            self.logger.debug(f"Retrieved {len(channels)} channels")
            return channels
            
        except Exception as e:
            self.logger.error(f"Failed to get channels: {e}")
            return []
    
    async def save_setting(self, key: str, value: str) -> None:
        """
        Save a setting to the database.
        
        Args:
            key: Setting key
            value: Setting value
        """
        try:
            await self._execute_query("""
                INSERT OR REPLACE INTO settings (key, value, updated_at)
                VALUES (?, ?, ?)
            """, (key, value, datetime.now()))
            
            self.logger.debug(f"Saved setting: {key}")
            
        except Exception as e:
            self.logger.error(f"Failed to save setting: {e}")
    
    async def get_setting(self, key: str, default: str = None) -> Optional[str]:
        """
        Get a setting from the database.
        
        Args:
            key: Setting key
            default: Default value if not found
            
        Returns:
            Setting value or default
        """
        try:
            cursor = await self._execute_query("""
                SELECT value FROM settings WHERE key = ?
            """, (key,))
            
            row = cursor.fetchone()
            if row:
                return row[0]
            else:
                return default
            
        except Exception as e:
            self.logger.error(f"Failed to get setting {key}: {e}")
            return default
    
    def _generate_message_id(self) -> str:
        """Generate a unique message ID."""
        import uuid
        return str(uuid.uuid4())
    
    async def close(self) -> None:
        """Close the database connection."""
        try:
            if self.connection:
                self.connection.close()
                self.connection = None
                self.logger.debug("Database connection closed")
        except Exception as e:
            self.logger.error(f"Error closing database: {e}")