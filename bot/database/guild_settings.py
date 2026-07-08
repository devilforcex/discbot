"""
Guild settings database operations for the Discord Music Bot.
Provides functions to get and update per-guild configuration.
"""

import logging
from typing import Optional

from bot.database.database import get_connection

logger = logging.getLogger(__name__)


def get_default_settings() -> dict:
    """Return default guild settings.

    Returns:
        Dictionary with default settings values.
    """
    return {
        "volume": 50,
        "autoplay": True,
        "announce_songs": True,
        "default_source": "ytsearch",
    }


def get(guild_id: str, db_path: str) -> dict:
    """Get settings for a guild, creating defaults if not exists.

    Args:
        guild_id: Discord guild ID.
        db_path: Path to the SQLite database file.

    Returns:
        Dictionary of guild settings.
    """
    conn = get_connection(db_path)
    cursor = conn.cursor()

    cursor.execute(
        "SELECT * FROM guild_settings WHERE guild_id = ?",
        (guild_id,),
    )
    row = cursor.fetchone()

    if row is None:
        # Create default settings
        defaults = get_default_settings()
        cursor.execute(
            """INSERT INTO guild_settings (guild_id, volume, autoplay, announce_songs, default_source)
               VALUES (?, ?, ?, ?, ?)""",
            (
                guild_id,
                defaults["volume"],
                int(defaults["autoplay"]),
                int(defaults["announce_songs"]),
                defaults["default_source"],
            ),
        )
        conn.commit()
        return dict(defaults)

    return dict(row)


def set(guild_id: str, db_path: str, **kwargs) -> dict:
    """Update specific settings fields for a guild.

    Args:
        guild_id: Discord guild ID.
        db_path: Path to the SQLite database file.
        **kwargs: Settings fields to update (volume, autoplay, announce_songs, default_source).

    Returns:
        Updated dictionary of guild settings.
    """
    conn = get_connection(db_path)
    cursor = conn.cursor()

    # Ensure settings row exists
    get(guild_id, db_path)

    allowed_fields = {"volume", "autoplay", "announce_songs", "default_source"}
    updates = {}
    for key, value in kwargs.items():
        if key in allowed_fields:
            # Convert booleans to integers for SQLite
            if isinstance(value, bool):
                updates[key] = int(value)
            else:
                updates[key] = value

    if updates:
        set_clause = ", ".join(f"{k} = ?" for k in updates.keys())
        values = list(updates.values())
        values.append(guild_id)

        cursor.execute(
            f"UPDATE guild_settings SET {set_clause}, updated_at = CURRENT_TIMESTAMP WHERE guild_id = ?",
            values,
        )
        conn.commit()
        logger.info("Updated guild settings for %s: %s", guild_id, updates)

    return get(guild_id, db_path)


def remove(guild_id: str, db_path: str) -> None:
    """Remove guild settings when the bot leaves a guild.

    Args:
        guild_id: Discord guild ID.
        db_path: Path to the SQLite database file.
    """
    conn = get_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM guild_settings WHERE guild_id = ?", (guild_id,))
    conn.commit()
    logger.info("Removed guild settings for %s", guild_id)