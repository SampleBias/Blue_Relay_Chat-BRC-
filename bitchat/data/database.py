"""
Database manager for bitchat RPi 4 client.

This module provides database operations using SQLite for persistent
storage of messages, peers, channels, and other data.
"""

import asyncio
import sqlite3
import aiosqlite
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
from contextlib import asynccontextmanager

from ..config.manager import ConfigManager
from ..utils.logging import get_logger
from ..exceptions import DatabaseError
from .models import Message, Peer, Channel, QueuedMessage, Identity, ConfigSetting


class DatabaseManager:
    """Manages SQLite database operations for the application."""
    
    def __init__(self, config_manager: ConfigManager) -> None:
        """
        Initialize the database manager.
        
        Args:
            config_manager: Configuration manager instance
        """
        self.config = config_manager
        self.logger = get_logger("database")
        self.db_path = config_manager.get_database_path()
        self._connection: Optional[aiosqlite.Connection] = None
        
        # Database configuration
        self.max_connections = config_manager.get("database.max_connections", 5)
        self.connection_timeout = config_manager.get("database.connection_timeout", 30)
        self.wal_mode = config_manager.get("database.wal_mode", True)
        self.foreign_keys = config_manager.get("database.foreign_keys", True)
    
    async def initialize(self) -> None:
        """Initialize the database and create tables if they don't exist."""
        try:
            # Ensure database directory exists
            Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
            
            # Connect to database
            await self.connect()
            
            # Enable WAL mode for better concurrency
            if self.wal_mode:
                await self.execute("PRAGMA journal_mode=WAL")
            
            # Enable foreign key constraints
            if self.foreign_keys:
                await self.execute("PRAGMA foreign_keys=ON")
            
            # Create tables
            await self._create_tables()
            
            self.logger.info(f"Database initialized at {self.db_path}")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize database: {e}")
            raise DatabaseError(f"Database initialization failed: {e}")
    
    async def connect(self) -> None:
        """Connect to the database."""
        if self._connection is None:
            try:
                self._connection = await aiosqlite.connect(
                    self.db_path,
                    timeout=self.connection_timeout
                )
                self._connection.row_factory = aiosqlite.Row
                self.logger.debug("Connected to database")
            except Exception as e:
                raise DatabaseError(f"Failed to connect to database: {e}")
    
    async def disconnect(self) -> None:
        """Disconnect from the database."""
        if self._connection:
            await self._connection.close()
            self._connection = None
            self.logger.debug("Disconnected from database")
    
    @asynccontextmanager
    async def transaction(self):
        """Context manager for database transactions."""
        if not self._connection:
            await self.connect()
        
        try:
            await self._connection.execute("BEGIN")
            yield
            await self._connection.commit()
        except Exception:
            await self._connection.rollback()
            raise
    
    async def execute(self, query: str, params: tuple = ()) -> aiosqlite.Cursor:
        """
        Execute a SQL query.
        
        Args:
            query: SQL query to execute
            params: Query parameters
            
        Returns:
            Cursor object
        """
        if not self._connection:
            await self.connect()
        
        try:
            return await self._connection.execute(query, params)
        except Exception as e:
            self.logger.error(f"Database query failed: {query}, params: {params}, error: {e}")
            raise DatabaseError(f"Query execution failed: {e}")
    
    async def execute_many(self, query: str, params_list: List[tuple]) -> None:
        """
        Execute a SQL query multiple times with different parameters.
        
        Args:
            query: SQL query to execute
            params_list: List of parameter tuples
        """
        if not self._connection:
            await self.connect()
        
        try:
            await self._connection.executemany(query, params_list)
        except Exception as e:
            self.logger.error(f"Database query failed: {query}, error: {e}")
            raise DatabaseError(f"Query execution failed: {e}")
    
    async def fetch_one(self, query: str, params: tuple = ()) -> Optional[sqlite3.Row]:
        """
        Fetch a single row from the database.
        
        Args:
            query: SQL query to execute
            params: Query parameters
            
        Returns:
            Row object or None if no rows found
        """
        cursor = await self.execute(query, params)
        return await cursor.fetchone()
    
    async def fetch_all(self, query: str, params: tuple = ()) -> List[sqlite3.Row]:
        """
        Fetch all rows from the database.
        
        Args:
            query: SQL query to execute
            params: Query parameters
            
        Returns:
            List of row objects
        """
        cursor = await self.execute(query, params)
        return await cursor.fetchall()
    
    async def _create_tables(self) -> None:
        """Create all database tables."""
        # Messages table
        await self.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id TEXT PRIMARY KEY,
                sender_id TEXT NOT NULL,
                recipient_id TEXT,
                channel_id TEXT,
                content TEXT NOT NULL,
                message_type TEXT NOT NULL DEFAULT 'text',
                transport_type TEXT,
                created_at TEXT NOT NULL,
                received_at TEXT,
                delivered_at TEXT,
                status TEXT NOT NULL DEFAULT 'pending',
                encrypted BOOLEAN NOT NULL DEFAULT 0,
                compressed BOOLEAN NOT NULL DEFAULT 0,
                metadata TEXT,
                FOREIGN KEY (sender_id) REFERENCES peers(id),
                FOREIGN KEY (recipient_id) REFERENCES peers(id),
                FOREIGN KEY (channel_id) REFERENCES channels(id)
            )
        """)
        
        # Peers table
        await self.execute("""
            CREATE TABLE IF NOT EXISTS peers (
                id TEXT PRIMARY KEY,
                public_key TEXT NOT NULL,
                last_seen TEXT NOT NULL,
                transport_type TEXT NOT NULL DEFAULT 'mesh',
                is_local BOOLEAN NOT NULL DEFAULT 1,
                status TEXT NOT NULL DEFAULT 'offline',
                metadata TEXT
            )
        """)
        
        # Channels table
        await self.execute("""
            CREATE TABLE IF NOT EXISTS channels (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                channel_type TEXT NOT NULL DEFAULT 'mesh',
                is_private BOOLEAN NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL,
                description TEXT,
                metadata TEXT
            )
        """)
        
        # Queued messages table
        await self.execute("""
            CREATE TABLE IF NOT EXISTS queued_messages (
                id TEXT PRIMARY KEY,
                message_id TEXT NOT NULL,
                transport_type TEXT NOT NULL,
                retry_count INTEGER NOT NULL DEFAULT 0,
                max_retries INTEGER NOT NULL DEFAULT 3,
                next_retry TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'active',
                priority INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL,
                metadata TEXT,
                FOREIGN KEY (message_id) REFERENCES messages(id) ON DELETE CASCADE
            )
        """)
        
        # Identity table
        await self.execute("""
            CREATE TABLE IF NOT EXISTS identity (
                id TEXT PRIMARY KEY,
                public_key TEXT NOT NULL,
                private_key TEXT NOT NULL,
                key_algorithm TEXT NOT NULL DEFAULT 'ed25519',
                created_at TEXT NOT NULL,
                last_used TEXT,
                metadata TEXT
            )
        """)
        
        # Config settings table
        await self.execute("""
            CREATE TABLE IF NOT EXISTS config_settings (
                key TEXT NOT NULL,
                section TEXT NOT NULL,
                value TEXT NOT NULL,
                description TEXT,
                data_type TEXT NOT NULL DEFAULT 'string',
                is_encrypted BOOLEAN NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                PRIMARY KEY (key, section)
            )
        """)
        
        # Create indexes for better performance
        await self._create_indexes()
    
    async def _create_indexes(self) -> None:
        """Create database indexes for better performance."""
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_messages_sender_id ON messages(sender_id)",
            "CREATE INDEX IF NOT EXISTS idx_messages_recipient_id ON messages(recipient_id)",
            "CREATE INDEX IF NOT EXISTS idx_messages_channel_id ON messages(channel_id)",
            "CREATE INDEX IF NOT EXISTS idx_messages_created_at ON messages(created_at)",
            "CREATE INDEX IF NOT EXISTS idx_messages_status ON messages(status)",
            "CREATE INDEX IF NOT EXISTS idx_peers_last_seen ON peers(last_seen)",
            "CREATE INDEX IF NOT EXISTS idx_peers_status ON peers(status)",
            "CREATE INDEX IF NOT EXISTS idx_queued_messages_next_retry ON queued_messages(next_retry)",
            "CREATE INDEX IF NOT EXISTS idx_queued_messages_status ON queued_messages(status)",
            "CREATE INDEX IF NOT EXISTS idx_queued_messages_priority ON queued_messages(priority DESC)",
        ]
        
        for index_query in indexes:
            await self.execute(index_query)
    
    # Message operations
    async def save_message(self, message: Message) -> None:
        """Save a message to the database."""
        query = """
            INSERT OR REPLACE INTO messages (
                id, sender_id, recipient_id, channel_id, content, message_type,
                transport_type, created_at, received_at, delivered_at, status,
                encrypted, compressed, metadata
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        params = (
            message.id,
            message.sender_id,
            message.recipient_id,
            message.channel_id,
            message.content,
            message.message_type.value,
            message.transport_type.value if message.transport_type else None,
            message.created_at.isoformat(),
            message.received_at.isoformat() if message.received_at else None,
            message.delivered_at.isoformat() if message.delivered_at else None,
            message.status.value,
            message.encrypted,
            message.compressed,
            str(message.metadata) if message.metadata else None,
        )
        
        await self.execute(query, params)
    
    async def get_message(self, message_id: str) -> Optional[Message]:
        """Get a message by ID."""
        query = "SELECT * FROM messages WHERE id = ?"
        row = await self.fetch_one(query, (message_id,))
        
        if row:
            return self._row_to_message(row)
        return None
    
    async def get_messages_by_channel(self, channel_id: str, limit: int = 100) -> List[Message]:
        """Get messages for a channel."""
        query = """
            SELECT * FROM messages 
            WHERE channel_id = ? 
            ORDER BY created_at DESC 
            LIMIT ?
        """
        rows = await self.fetch_all(query, (channel_id, limit))
        return [self._row_to_message(row) for row in rows]
    
    async def get_messages_by_peer(self, peer_id: str, limit: int = 100) -> List[Message]:
        """Get messages for a peer."""
        query = """
            SELECT * FROM messages 
            WHERE sender_id = ? OR recipient_id = ? 
            ORDER BY created_at DESC 
            LIMIT ?
        """
        rows = await self.fetch_all(query, (peer_id, peer_id, limit))
        return [self._row_to_message(row) for row in rows]
    
    # Peer operations
    async def save_peer(self, peer: Peer) -> None:
        """Save a peer to the database."""
        query = """
            INSERT OR REPLACE INTO peers (
                id, public_key, last_seen, transport_type, is_local, status, metadata
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """
        
        params = (
            peer.id,
            peer.public_key,
            peer.last_seen.isoformat(),
            peer.transport_type.value,
            peer.is_local,
            peer.status.value,
            str(peer.metadata) if peer.metadata else None,
        )
        
        await self.execute(query, params)
    
    async def get_peer(self, peer_id: str) -> Optional[Peer]:
        """Get a peer by ID."""
        query = "SELECT * FROM peers WHERE id = ?"
        row = await self.fetch_one(query, (peer_id,))
        
        if row:
            return self._row_to_peer(row)
        return None
    
    async def get_online_peers(self, timeout_minutes: int = 5) -> List[Peer]:
        """Get all online peers."""
        cutoff_time = (datetime.now() - timedelta(minutes=timeout_minutes)).isoformat()
        query = "SELECT * FROM peers WHERE last_seen > ? AND status = 'online'"
        rows = await self.fetch_all(query, (cutoff_time,))
        return [self._row_to_peer(row) for row in rows]
    
    # Channel operations
    async def save_channel(self, channel: Channel) -> None:
        """Save a channel to the database."""
        query = """
            INSERT OR REPLACE INTO channels (
                id, name, channel_type, is_private, created_at, description, metadata
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """
        
        params = (
            channel.id,
            channel.name,
            channel.channel_type.value,
            channel.is_private,
            channel.created_at.isoformat(),
            channel.description,
            str(channel.metadata) if channel.metadata else None,
        )
        
        await self.execute(query, params)
    
    async def get_channel(self, channel_id: str) -> Optional[Channel]:
        """Get a channel by ID."""
        query = "SELECT * FROM channels WHERE id = ?"
        row = await self.fetch_one(query, (channel_id,))
        
        if row:
            return self._row_to_channel(row)
        return None
    
    async def get_channels(self, channel_type: Optional[ChannelType] = None) -> List[Channel]:
        """Get all channels, optionally filtered by type."""
        if channel_type:
            query = "SELECT * FROM channels WHERE channel_type = ? ORDER BY name"
            rows = await self.fetch_all(query, (channel_type.value,))
        else:
            query = "SELECT * FROM channels ORDER BY name"
            rows = await self.fetch_all(query)
        
        return [self._row_to_channel(row) for row in rows]
    
    # Queued message operations
    async def save_queued_message(self, queued_message: QueuedMessage) -> None:
        """Save a queued message to the database."""
        query = """
            INSERT OR REPLACE INTO queued_messages (
                id, message_id, transport_type, retry_count, max_retries,
                next_retry, status, priority, created_at, metadata
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        params = (
            queued_message.id,
            queued_message.message_id,
            queued_message.transport_type.value,
            queued_message.retry_count,
            queued_message.max_retries,
            queued_message.next_retry.isoformat(),
            queued_message.status.value,
            queued_message.priority,
            queued_message.created_at.isoformat(),
            str(queued_message.metadata) if queued_message.metadata else None,
        )
        
        await self.execute(query, params)
    
    async def get_pending_queued_messages(self, limit: int = 50) -> List[QueuedMessage]:
        """Get pending queued messages that should be retried."""
        now = datetime.now().isoformat()
        query = """
            SELECT * FROM queued_messages 
            WHERE status = 'active' AND next_retry <= ? 
            ORDER BY priority DESC, created_at ASC 
            LIMIT ?
        """
        rows = await self.fetch_all(query, (now, limit))
        return [self._row_to_queued_message(row) for row in rows]
    
    # Utility methods
    def _row_to_message(self, row: sqlite3.Row) -> Message:
        """Convert a database row to a Message object."""
        return Message.from_dict(dict(row))
    
    def _row_to_peer(self, row: sqlite3.Row) -> Peer:
        """Convert a database row to a Peer object."""
        return Peer.from_dict(dict(row))
    
    def _row_to_channel(self, row: sqlite3.Row) -> Channel:
        """Convert a database row to a Channel object."""
        return Channel.from_dict(dict(row))
    
    def _row_to_queued_message(self, row: sqlite3.Row) -> QueuedMessage:
        """Convert a database row to a QueuedMessage object."""
        return QueuedMessage.from_dict(dict(row))
    
    async def cleanup_old_messages(self, days: int = 30) -> int:
        """Clean up old messages from the database."""
        cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()
        
        with await self.transaction():
            # Delete old messages
            cursor = await self.execute(
                "DELETE FROM messages WHERE created_at < ?", (cutoff_date,)
            )
            deleted_count = cursor.rowcount
            
            # Delete orphaned queued messages
            await self.execute("""
                DELETE FROM queued_messages 
                WHERE message_id NOT IN (SELECT id FROM messages)
            """)
        
        self.logger.info(f"Cleaned up {deleted_count} old messages")
        return deleted_count
    
    async def get_database_stats(self) -> Dict[str, Any]:
        """Get database statistics."""
        stats = {}
        
        # Count tables
        tables = ["messages", "peers", "channels", "queued_messages"]
        for table in tables:
            cursor = await self.execute(f"SELECT COUNT(*) FROM {table}")
            row = await cursor.fetchone()
            stats[f"{table}_count"] = row[0] if row else 0
        
        # Database size
        db_size = Path(self.db_path).stat().st_size if Path(self.db_path).exists() else 0
        stats["database_size_bytes"] = db_size
        stats["database_size_mb"] = round(db_size / (1024 * 1024), 2)
        
        return stats