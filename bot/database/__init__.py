"""
Database package for the Discord Music Bot.
Provides SQLite (local) and PostgreSQL (cloud) support.
"""

from bot.database.database import (
    close_connection,
    get_connection,
    initialize_database,
)
from bot.database.repository import DatabaseRepository, create_repository

__all__ = [
    "close_connection",
    "get_connection",
    "initialize_database",
    "DatabaseRepository",
    "create_repository",
]
