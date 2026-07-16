"""
Database module for the Discord Music Bot.
Provides SQLite connection management, table creation, and migration helpers.
"""

import contextlib
import logging
import sqlite3
import threading
from pathlib import Path

logger = logging.getLogger(__name__)

_local = threading.local()
_registry_lock = threading.Lock()
_connection_registry: dict[str, list[sqlite3.Connection]] = {}


def _connection_cache() -> dict[str, sqlite3.Connection]:
    """Return the thread-local connection cache keyed by resolved DB path."""
    if not hasattr(_local, "connections") or _local.connections is None:
        _local.connections = {}
    return _local.connections


def _register_connection(cache_key: str, conn: sqlite3.Connection) -> None:
    with _registry_lock:
        connections = _connection_registry.setdefault(cache_key, [])
        if conn not in connections:
            connections.append(conn)


def _unregister_connection(cache_key: str, conn: sqlite3.Connection) -> None:
    with _registry_lock:
        connections = _connection_registry.get(cache_key)
        if connections is None:
            return
        with contextlib.suppress(ValueError):
            connections.remove(conn)
        if not connections:
            _connection_registry.pop(cache_key, None)


def _registered_connections(cache_key: str) -> list[sqlite3.Connection]:
    with _registry_lock:
        return list(_connection_registry.get(cache_key, []))


def _close_registered_connection(cache_key: str, conn: sqlite3.Connection) -> None:
    try:
        conn.close()
    except sqlite3.ProgrammingError as exc:
        logger.debug("Database connection already closed or unavailable: %s", exc)
    finally:
        _unregister_connection(cache_key, conn)


def get_connection(db_path: str) -> sqlite3.Connection:
    """Get a thread-local database connection.

    Args:
        db_path: Path to the SQLite database file.

    Returns:
        A SQLite connection object with row factory set.
    """
    # Resolve the path so equivalent inputs (e.g. ./data/db.sqlite and
    # data/db.sqlite) share one connection, while different databases don't
    # accidentally reuse the first connection opened in this thread.
    db_path_obj = Path(db_path).expanduser().resolve()
    db_path_obj.parent.mkdir(parents=True, exist_ok=True)
    cache = _connection_cache()
    cache_key = str(db_path_obj)

    conn = cache.get(cache_key)
    if conn is None:
        conn = sqlite3.connect(str(db_path_obj), check_same_thread=False)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        conn.execute("PRAGMA busy_timeout=5000")
        cache[cache_key] = conn
        _register_connection(cache_key, conn)
        logger.debug("Database connection established: %s", db_path_obj)
    return conn


def close_connection(db_path: str | None = None) -> None:
    """Close thread-local database connection(s).

    Args:
        db_path: Optional database path. If provided, only that connection is
            closed; otherwise all connections opened in the current thread are
            closed.
    """
    cache = _connection_cache()
    if db_path is not None:
        cache_key = str(Path(db_path).expanduser().resolve())
        conn = cache.pop(cache_key, None)
        if conn is not None:
            _close_registered_connection(cache_key, conn)
        for registered in _registered_connections(cache_key):
            _close_registered_connection(cache_key, registered)
        logger.debug("Database connections closed: %s", cache_key)
        return

    for cache_key, conn in list(cache.items()):
        _close_registered_connection(cache_key, conn)
        logger.debug("Database connection closed: %s", cache_key)
    cache.clear()


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
