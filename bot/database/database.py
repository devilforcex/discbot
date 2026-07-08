"""
Database module for the Discord Music Bot.
Provides SQLite connection management, table creation, and migration helpers.
"""

import logging
import sqlite3
import threading
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

_local = threading.local()


def get_connection(db_path: str) -> sqlite3.Connection:
    """Get a thread-local database connection.

    Args:
        db_path: Path to the SQLite database file.

    Returns:
        A SQLite connection object with row factory set.
    """
    if not hasattr(_local, "conn") or _local.conn is None:
        # Ensure directory exists
        db_path_obj = Path(db_path)
        db_path_obj.parent.mkdir(parents=True, exist_ok=True)

        conn = sqlite3.connect(str(db_path_obj))
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        conn.execute("PRAGMA busy_timeout=5000")
        _local.conn = conn
        logger.debug("Database connection established: %s", db_path)
    return _local.conn


def close_connection() -> None:
    """Close the thread-local database connection if open."""
    if hasattr(_local, "conn") and _local.conn is not None:
        _local.conn.close()
        _local.conn = None
        logger.debug("Database connection closed")


def initialize_database(db_path: str) -> sqlite3.Connection:
    """Initialize the database, creating tables if they don't exist.

    Args:
        db_path: Path to the SQLite database file.

    Returns:
        The database connection.
    """
    conn = get_connection(db_path)
    _create_tables(conn)
    logger.info("Database initialized: %s", db_path)
    return conn


def _create_tables(conn: sqlite3.Connection) -> None:
    """Create all required tables if they don't exist.

    Args:
        conn: Database connection.
    """
    cursor = conn.cursor()

    # Guild settings
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS guild_settings (
            guild_id TEXT PRIMARY KEY,
            volume INTEGER NOT NULL DEFAULT 50,
            autoplay INTEGER NOT NULL DEFAULT 1,
            announce_songs INTEGER NOT NULL DEFAULT 1,
            default_source TEXT NOT NULL DEFAULT 'ytsearch',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # User favorites
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_favorites (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            title TEXT NOT NULL,
            author TEXT NOT NULL,
            uri TEXT NOT NULL,
            identifier TEXT NOT NULL,
            length INTEGER NOT NULL,
            artwork_url TEXT,
            added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, identifier)
        )
    """)

    # Playlists
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS playlists (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            playlist_id TEXT NOT NULL UNIQUE,
            user_id TEXT NOT NULL,
            guild_id TEXT NOT NULL,
            name TEXT NOT NULL,
            description TEXT DEFAULT '',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Playlist tracks
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS playlist_tracks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            playlist_id TEXT NOT NULL,
            position INTEGER NOT NULL,
            title TEXT NOT NULL,
            author TEXT NOT NULL,
            uri TEXT NOT NULL,
            identifier TEXT NOT NULL,
            length INTEGER NOT NULL,
            artwork_url TEXT,
            added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            added_by TEXT NOT NULL,
            FOREIGN KEY (playlist_id) REFERENCES playlists(playlist_id) ON DELETE CASCADE
        )
    """)

    # Playback history
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS playback_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            guild_id TEXT NOT NULL,
            user_id TEXT NOT NULL,
            title TEXT NOT NULL,
            author TEXT NOT NULL,
            uri TEXT NOT NULL,
            identifier TEXT NOT NULL,
            length INTEGER NOT NULL,
            played_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Create indexes
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_favorites_user
        ON user_favorites(user_id)
    """)
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_playlists_user
        ON playlists(user_id)
    """)
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_playlist_tracks_playlist
        ON playlist_tracks(playlist_id)
    """)
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_history_guild
        ON playback_history(guild_id)
    """)
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_playlist_tracks_position
        ON playlist_tracks(playlist_id, position)
    """)

    # Approved users (access control whitelist)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS approved_users (
            user_id TEXT PRIMARY KEY,
            username TEXT NOT NULL DEFAULT '',
            display_name TEXT NOT NULL DEFAULT '',
            added_by TEXT NOT NULL,
            added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Access requests (self-registration)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS access_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            username TEXT NOT NULL DEFAULT '',
            display_name TEXT NOT NULL DEFAULT '',
            guild TEXT NOT NULL DEFAULT '',
            requested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            status TEXT NOT NULL DEFAULT 'pending'
        )
    """)

    # Blacklisted users
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS blacklisted_users (
            user_id TEXT PRIMARY KEY,
            username TEXT NOT NULL DEFAULT '',
            display_name TEXT NOT NULL DEFAULT '',
            added_by TEXT NOT NULL,
            added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Audit logs
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS audit_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            action TEXT NOT NULL,
            target_user_id TEXT NOT NULL DEFAULT '',
            target_username TEXT NOT NULL DEFAULT '',
            moderator_id TEXT NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Bot settings (key-value store for 24/7 mode, etc.)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS bot_settings (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL DEFAULT ''
        )
    """)

    # Create indexes for new tables
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_access_requests_status
        ON access_requests(status)
    """)
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_audit_logs_action
        ON audit_logs(action)
    """)

    conn.commit()
    logger.debug("All database tables created/verified")
