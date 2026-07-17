"""
PostgreSQL connection manager for DrusaBoT.
Used when DATABASE_URL is set (cloud deployment / PostgreSQL).
Falls back to SQLite when DATABASE_URL is not set.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    import asyncpg

logger = logging.getLogger(__name__)

try:
    import asyncpg as _asyncpg

    HAS_ASYNCPG = True
except ImportError:
    HAS_ASYNCPG = False
    _asyncpg = None


class PostgresManager:
    """Manages PostgreSQL connection pool for the bot."""

    def __init__(self, dsn: str | None = None):
        self._dsn = dsn
        self._pool: asyncpg.Pool | None = None

    @property
    def is_connected(self) -> bool:
        return self._pool is not None and not self._pool._closed  # type: ignore[union-attr]

    async def connect(self, dsn: str | None = None) -> bool:
        """Connect to PostgreSQL using DSN."""
        if not HAS_ASYNCPG:
            logger.warning("asyncpg not installed. Install with: pip install asyncpg")
            return False

        connection_dsn = dsn or self._dsn
        if not connection_dsn:
            logger.warning("No DATABASE_URL provided for PostgreSQL connection")
            return False

        try:
            self._pool = await _asyncpg.create_pool(  # type: ignore[union-attr]
                dsn=connection_dsn,
                min_size=2,
                max_size=10,
                command_timeout=60,
            )
            logger.info("Connected to PostgreSQL")
            return True
        except Exception as e:
            logger.error("Failed to connect to PostgreSQL: %s", e)
            return False

    async def disconnect(self) -> None:
        """Close the connection pool."""
        if self._pool:
            await self._pool.close()
            self._pool = None
            logger.info("PostgreSQL connection closed")

    async def execute(self, query: str, *args: Any) -> Any:
        """Execute a query and return the result."""
        if not self._pool:
            raise RuntimeError("PostgreSQL pool not initialized")
        async with self._pool.acquire() as conn:
            return await conn.execute(query, *args)

    async def fetch(self, query: str, *args: Any) -> list[asyncpg.Record]:
        """Fetch multiple rows."""
        if not self._pool:
            raise RuntimeError("PostgreSQL pool not initialized")
        async with self._pool.acquire() as conn:
            return await conn.fetch(query, *args)  # type: ignore[return-value]

    async def fetchrow(self, query: str, *args: Any) -> asyncpg.Record | None:
        """Fetch a single row."""
        if not self._pool:
            raise RuntimeError("PostgreSQL pool not initialized")
        async with self._pool.acquire() as conn:
            return await conn.fetchrow(query, *args)  # type: ignore[return-value]

    async def fetchval(self, query: str, *args: Any) -> Any:
        """Fetch a single value."""
        if not self._pool:
            raise RuntimeError("PostgreSQL pool not initialized")
        async with self._pool.acquire() as conn:
            return await conn.fetchval(query, *args)


# Global instance
_postgres: PostgresManager | None = None


def get_postgres() -> PostgresManager | None:
    """Get the global PostgreSQL manager instance."""
    global _postgres
    return _postgres


def set_postgres(pg: PostgresManager) -> None:
    """Set the global PostgreSQL manager instance."""
    global _postgres
    _postgres = pg
