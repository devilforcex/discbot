"""
Database repository abstraction layer.
Provides a unified interface for SQLite (local) and PostgreSQL (cloud).
Auto-detects which backend to use based on DATABASE_URL config.
"""

from __future__ import annotations

import logging
from typing import Any

from bot.database.database import get_connection, initialize_database
from bot.database.postgres import PostgresManager, set_postgres

logger = logging.getLogger(__name__)

DB_BACKEND_SQLITE = "sqlite"
DB_BACKEND_POSTGRES = "postgres"


class DatabaseRepository:
    """Unified database repository that works with SQLite or PostgreSQL."""

    def __init__(self, db_path: str, database_url: str | None = None):
        self._db_path = db_path
        self._database_url = database_url
        self._backend: str = DB_BACKEND_SQLITE
        self._postgres: PostgresManager | None = None

    @property
    def backend(self) -> str:
        """Get the active database backend type."""
        return self._backend

    @property
    def is_postgres(self) -> bool:
        """Check if using PostgreSQL backend."""
        return self._backend == DB_BACKEND_POSTGRES

    async def initialize(self) -> bool:
        """Initialize the database backend.

        Returns True if PostgreSQL is available and connected,
        False if falling back to SQLite.
        """
        # Try PostgreSQL first if DATABASE_URL is set
        if self._database_url:
            pg = PostgresManager(self._database_url)
            connected = await pg.connect()
            if connected:
                self._postgres = pg
                self._backend = DB_BACKEND_POSTGRES
                set_postgres(pg)
                await self._create_tables_postgres()
                logger.info("Database backend: PostgreSQL")
                return True
            else:
                logger.warning("PostgreSQL connection failed, falling back to SQLite")

        # Fall back to SQLite
        self._backend = DB_BACKEND_SQLITE
        initialize_database(self._db_path)
        logger.info("Database backend: SQLite (%s)", self._db_path)
        return False

    async def shutdown(self) -> None:
        """Shutdown the database backend."""
        if self._postgres:
            await self._postgres.disconnect()
        else:
            from bot.database.database import close_connection

            close_connection(self._db_path)

    # --- Query helpers ---

    async def execute(self, query: str, *args: Any) -> Any:
        """Execute a query (write operation)."""
        if self._postgres:
            return await self._postgres.execute(query, *args)
        else:
            conn = get_connection(self._db_path)
            cursor = conn.cursor()
            cursor.execute(query, args)
            conn.commit()
            return cursor

    async def fetch(self, query: str, *args: Any) -> list[dict[str, Any]]:
        """Fetch multiple rows as dicts."""
        if self._postgres:
            records = await self._postgres.fetch(query, *args)
            return [dict(r) for r in records]
        else:
            conn = get_connection(self._db_path)
            cursor = conn.cursor()
            cursor.execute(query, args)
            return [dict(row) for row in cursor.fetchall()]

    async def fetchrow(self, query: str, *args: Any) -> dict[str, Any] | None:
        """Fetch a single row as dict."""
        if self._postgres:
            record = await self._postgres.fetchrow(query, *args)
            return dict(record) if record else None
        else:
            conn = get_connection(self._db_path)
            cursor = conn.cursor()
            cursor.execute(query, args)
            row = cursor.fetchone()
            return dict(row) if row else None

    async def fetchval(self, query: str, *args: Any) -> Any:
        """Fetch a single value."""
        if self._postgres:
            return await self._postgres.fetchval(query, *args)
        else:
            conn = get_connection(self._db_path)
            cursor = conn.cursor()
            cursor.execute(query, args)
            row = cursor.fetchone()
            return row[0] if row else None

    # --- PostgreSQL table creation ---

    async def _create_tables_postgres(self) -> None:
        """Create all required tables in PostgreSQL."""
        if not self._postgres:
            return

        # Guild settings
        await self._postgres.execute("""
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
        await self._postgres.execute("""
            CREATE TABLE IF NOT EXISTS user_favorites (
                id SERIAL PRIMARY KEY,
                user_id TEXT NOT NULL,
                title TEXT NOT NULL,
                author TEXT NOT NULL,
                uri TEXT NOT NULL,
                identifier TEXT NOT NULL,
                length BIGINT NOT NULL,
                artwork_url TEXT,
                added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, identifier)
            )
        """)

        # Playlists
        await self._postgres.execute("""
            CREATE TABLE IF NOT EXISTS playlists (
                id SERIAL PRIMARY KEY,
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
        await self._postgres.execute("""
            CREATE TABLE IF NOT EXISTS playlist_tracks (
                id SERIAL PRIMARY KEY,
                playlist_id TEXT NOT NULL,
                position INTEGER NOT NULL,
                title TEXT NOT NULL,
                author TEXT NOT NULL,
                uri TEXT NOT NULL,
                identifier TEXT NOT NULL,
                length BIGINT NOT NULL,
                artwork_url TEXT,
                added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                added_by TEXT NOT NULL,
                FOREIGN KEY (playlist_id) REFERENCES playlists(playlist_id) ON DELETE CASCADE
            )
        """)

        # Playback history
        await self._postgres.execute("""
            CREATE TABLE IF NOT EXISTS playback_history (
                id SERIAL PRIMARY KEY,
                guild_id TEXT NOT NULL,
                user_id TEXT NOT NULL,
                title TEXT NOT NULL,
                author TEXT NOT NULL,
                uri TEXT NOT NULL,
                identifier TEXT NOT NULL,
                length BIGINT NOT NULL,
                played_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Approved users (access control whitelist)
        await self._postgres.execute("""
            CREATE TABLE IF NOT EXISTS approved_users (
                user_id TEXT PRIMARY KEY,
                username TEXT NOT NULL DEFAULT '',
                display_name TEXT NOT NULL DEFAULT '',
                added_by TEXT NOT NULL,
                added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Access requests
        await self._postgres.execute("""
            CREATE TABLE IF NOT EXISTS access_requests (
                id SERIAL PRIMARY KEY,
                user_id TEXT NOT NULL,
                username TEXT NOT NULL DEFAULT '',
                display_name TEXT NOT NULL DEFAULT '',
                guild TEXT NOT NULL DEFAULT '',
                requested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status TEXT NOT NULL DEFAULT 'pending'
            )
        """)

        # Blacklisted users
        await self._postgres.execute("""
            CREATE TABLE IF NOT EXISTS blacklisted_users (
                user_id TEXT PRIMARY KEY,
                username TEXT NOT NULL DEFAULT '',
                display_name TEXT NOT NULL DEFAULT '',
                added_by TEXT NOT NULL,
                added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Audit logs
        await self._postgres.execute("""
            CREATE TABLE IF NOT EXISTS audit_logs (
                id SERIAL PRIMARY KEY,
                action TEXT NOT NULL,
                target_user_id TEXT NOT NULL DEFAULT '',
                target_username TEXT NOT NULL DEFAULT '',
                moderator_id TEXT NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Bot settings (key-value store)
        await self._postgres.execute("""
            CREATE TABLE IF NOT EXISTS bot_settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL DEFAULT ''
            )
        """)

        # Create indexes
        await self._postgres.execute(
            "CREATE INDEX IF NOT EXISTS idx_favorites_user ON user_favorites(user_id)"
        )
        await self._postgres.execute(
            "CREATE INDEX IF NOT EXISTS idx_playlists_user ON playlists(user_id)"
        )
        await self._postgres.execute(
            "CREATE INDEX IF NOT EXISTS idx_playlist_tracks_playlist ON playlist_tracks(playlist_id)"
        )
        await self._postgres.execute(
            "CREATE INDEX IF NOT EXISTS idx_history_guild ON playback_history(guild_id)"
        )
        await self._postgres.execute(
            "CREATE INDEX IF NOT EXISTS idx_playlist_tracks_position ON playlist_tracks(playlist_id, position)"
        )
        await self._postgres.execute(
            "CREATE INDEX IF NOT EXISTS idx_access_requests_status ON access_requests(status)"
        )
        await self._postgres.execute(
            "CREATE INDEX IF NOT EXISTS idx_audit_logs_action ON audit_logs(action)"
        )

        logger.info("PostgreSQL tables created/verified")


# Global repository instance
_repository: DatabaseRepository | None = None


def get_repository() -> DatabaseRepository | None:
    """Get the global repository instance."""
    global _repository
    return _repository


def set_repository(repo: DatabaseRepository) -> None:
    """Set the global repository instance."""
    global _repository
    _repository = repo


async def create_repository(db_path: str, database_url: str | None = None) -> DatabaseRepository:
    """Create and initialize a database repository.

    Args:
        db_path: Path to SQLite database file (used as fallback).
        database_url: PostgreSQL connection string (optional).

    Returns:
        Initialized DatabaseRepository instance.
    """
    repo = DatabaseRepository(db_path, database_url)
    await repo.initialize()
    set_repository(repo)
    return repo
