"""
Playback history database operations for the Discord Music Bot.
Provides functions to record and query playback history.
"""

import logging
from typing import Optional

from bot.database.database import get_connection

logger = logging.getLogger(__name__)


def add(
    guild_id: str,
    user_id: str,
    title: str,
    author: str,
    uri: str,
    identifier: str,
    length: int,
    db_path: str = "data/musicbot.db",
) -> None:
    """Record a track playback in history.

    Args:
        guild_id: Discord guild ID where the track was played.
        user_id: Discord user ID who requested the track.
        title: Track title.
        author: Track author/artist.
        uri: Track URL.
        identifier: Track identifier.
        length: Duration in milliseconds.
        db_path: Path to the SQLite database file.
    """
    conn = get_connection(db_path)
    cursor = conn.cursor()

    cursor.execute(
        """INSERT INTO playback_history (guild_id, user_id, title, author, uri, identifier, length)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (guild_id, user_id, title, author, uri, identifier, length),
    )
    conn.commit()
    logger.debug("Recorded playback: %s in guild %s", title, guild_id)


def get_recent(
    guild_id: str,
    limit: int = 20,
    db_path: str = "data/musicbot.db",
) -> list[dict]:
    """Get recent playback history for a guild.

    Args:
        guild_id: Discord guild ID.
        limit: Maximum number of entries to return.
        db_path: Path to the SQLite database file.

    Returns:
        List of recent playback history entries.
    """
    conn = get_connection(db_path)
    cursor = conn.cursor()

    cursor.execute(
        """SELECT * FROM playback_history
           WHERE guild_id = ?
           ORDER BY played_at DESC
           LIMIT ?""",
        (guild_id, limit),
    )

    return [dict(row) for row in cursor.fetchall()]


def get_stats(
    guild_id: str,
    db_path: str = "data/musicbot.db",
) -> dict:
    """Get playback statistics for a guild.

    Args:
        guild_id: Discord guild ID.
        db_path: Path to the SQLite database file.

    Returns:
        Dictionary with total plays, unique tracks, and top tracks.
    """
    conn = get_connection(db_path)
    cursor = conn.cursor()

    # Total plays
    cursor.execute(
        "SELECT COUNT(*) FROM playback_history WHERE guild_id = ?",
        (guild_id,),
    )
    total_plays = cursor.fetchone()[0]

    # Unique tracks
    cursor.execute(
        "SELECT COUNT(DISTINCT identifier) FROM playback_history WHERE guild_id = ?",
        (guild_id,),
    )
    unique_tracks = cursor.fetchone()[0]

    # Top 10 most played tracks
    cursor.execute(
        """SELECT title, author, COUNT(*) as play_count
           FROM playback_history
           WHERE guild_id = ?
           GROUP BY identifier
           ORDER BY play_count DESC
           LIMIT 10""",
        (guild_id,),
    )
    top_tracks = [dict(row) for row in cursor.fetchall()]

    return {
        "total_plays": total_plays,
        "unique_tracks": unique_tracks,
        "top_tracks": top_tracks,
    }


def clear_guild_history(
    guild_id: str,
    db_path: str = "data/musicbot.db",
) -> None:
    """Clear all playback history for a guild.

    Args:
        guild_id: Discord guild ID.
        db_path: Path to the SQLite database file.
    """
    conn = get_connection(db_path)
    cursor = conn.cursor()

    cursor.execute(
        "DELETE FROM playback_history WHERE guild_id = ?",
        (guild_id,),
    )
    conn.commit()
    logger.info("Cleared playback history for guild %s", guild_id)