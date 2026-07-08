"""
Playlist database operations for the Discord Music Bot.
Provides CRUD functions for user-created playlists.
"""

import logging
import uuid
from typing import Optional

from bot.database.database import get_connection

logger = logging.getLogger(__name__)

_MAX_TRACKS_PER_PLAYLIST = 200


def create_playlist(
    user_id: str,
    guild_id: str,
    name: str,
    description: str = "",
    db_path: str = "data/musicbot.db",
) -> Optional[str]:
    """Create a new playlist.

    Args:
        user_id: Discord user ID of the creator.
        guild_id: Discord guild ID.
        name: Playlist name.
        description: Optional playlist description.
        db_path: Path to the SQLite database file.

    Returns:
        The playlist_id (UUID) if created, None if name already exists.
    """
    conn = get_connection(db_path)
    cursor = conn.cursor()

    # Check if user already has a playlist with this name
    cursor.execute(
        "SELECT 1 FROM playlists WHERE user_id = ? AND name = ?",
        (user_id, name),
    )
    if cursor.fetchone():
        logger.warning("Playlist '%s' already exists for user %s", name, user_id)
        return None

    playlist_id = str(uuid.uuid4())
    cursor.execute(
        """INSERT INTO playlists (playlist_id, user_id, guild_id, name, description)
           VALUES (?, ?, ?, ?, ?)""",
        (playlist_id, user_id, guild_id, name, description),
    )
    conn.commit()
    logger.info("Created playlist '%s' (%s) for user %s", name, playlist_id, user_id)
    return playlist_id


def add_track(
    playlist_id: str,
    title: str,
    author: str,
    uri: str,
    identifier: str,
    length: int,
    added_by: str,
    artwork_url: Optional[str] = None,
    db_path: str = "data/musicbot.db",
) -> bool:
    """Add a track to a playlist.

    Args:
        playlist_id: The playlist's UUID.
        title: Track title.
        author: Track author.
        uri: Track URL.
        identifier: Track identifier.
        length: Duration in milliseconds.
        added_by: Discord user ID who added the track.
        artwork_url: Optional thumbnail URL.
        db_path: Path to the SQLite database file.

    Returns:
        True if added, False if playlist full or not found.
    """
    conn = get_connection(db_path)
    cursor = conn.cursor()

    # Check playlist exists
    cursor.execute("SELECT 1 FROM playlists WHERE playlist_id = ?", (playlist_id,))
    if not cursor.fetchone():
        logger.warning("Playlist %s not found", playlist_id)
        return False

    # Check track limit
    cursor.execute(
        "SELECT COUNT(*) FROM playlist_tracks WHERE playlist_id = ?",
        (playlist_id,),
    )
    count = cursor.fetchone()[0]
    if count >= _MAX_TRACKS_PER_PLAYLIST:
        logger.warning("Playlist %s is full (%d tracks)", playlist_id, count)
        return False

    # Get next position
    next_pos = count + 1

    cursor.execute(
        """INSERT INTO playlist_tracks (playlist_id, position, title, author, uri, identifier, length, artwork_url, added_by)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (playlist_id, next_pos, title, author, uri, identifier, length, artwork_url, added_by),
    )
    conn.commit()

    # Update playlist timestamp
    cursor.execute(
        "UPDATE playlists SET updated_at = CURRENT_TIMESTAMP WHERE playlist_id = ?",
        (playlist_id,),
    )
    conn.commit()

    logger.info("Added track '%s' to playlist %s (position %d)", title, playlist_id, next_pos)
    return True


def remove_track(
    playlist_id: str,
    position: int,
    user_id: str,
    db_path: str = "data/musicbot.db",
) -> bool:
    """Remove a track from a playlist by position.

    Args:
        playlist_id: The playlist's UUID.
        position: Track position (1-indexed).
        user_id: Discord user ID (must be owner).
        db_path: Path to the SQLite database file.

    Returns:
        True if removed, False if not found or unauthorized.
    """
    conn = get_connection(db_path)
    cursor = conn.cursor()

    # Check ownership
    cursor.execute(
        "SELECT user_id FROM playlists WHERE playlist_id = ?",
        (playlist_id,),
    )
    row = cursor.fetchone()
    if not row or row["user_id"] != user_id:
        logger.warning("User %s not authorized to modify playlist %s", user_id, playlist_id)
        return False

    # Delete the track
    cursor.execute(
        "DELETE FROM playlist_tracks WHERE playlist_id = ? AND position = ?",
        (playlist_id, position),
    )
    if cursor.rowcount == 0:
        return False

    # Reorder remaining tracks
    cursor.execute(
        """UPDATE playlist_tracks SET position = position - 1
           WHERE playlist_id = ? AND position > ?""",
        (playlist_id, position),
    )
    conn.commit()

    # Update playlist timestamp
    cursor.execute(
        "UPDATE playlists SET updated_at = CURRENT_TIMESTAMP WHERE playlist_id = ?",
        (playlist_id,),
    )
    conn.commit()

    logger.info("Removed track at position %d from playlist %s", position, playlist_id)
    return True


def get_playlist(
    playlist_id: str,
    db_path: str = "data/musicbot.db",
) -> Optional[dict]:
    """Get a playlist with all its tracks.

    Args:
        playlist_id: The playlist's UUID.
        db_path: Path to the SQLite database file.

    Returns:
        Dictionary with playlist info and tracks list, or None if not found.
    """
    conn = get_connection(db_path)
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM playlists WHERE playlist_id = ?", (playlist_id,))
    playlist_row = cursor.fetchone()
    if not playlist_row:
        return None

    playlist = dict(playlist_row)

    # Get tracks
    cursor.execute(
        """SELECT * FROM playlist_tracks
           WHERE playlist_id = ?
           ORDER BY position ASC""",
        (playlist_id,),
    )
    playlist["tracks"] = [dict(row) for row in cursor.fetchall()]
    playlist["track_count"] = len(playlist["tracks"])

    return playlist


def list_user_playlists(
    user_id: str,
    db_path: str = "data/musicbot.db",
) -> list[dict]:
    """List all playlists for a user.

    Args:
        user_id: Discord user ID.
        db_path: Path to the SQLite database file.

    Returns:
        List of playlist dictionaries with track counts.
    """
    conn = get_connection(db_path)
    cursor = conn.cursor()

    cursor.execute(
        """SELECT p.*, COUNT(pt.id) as track_count
           FROM playlists p
           LEFT JOIN playlist_tracks pt ON p.playlist_id = pt.playlist_id
           WHERE p.user_id = ?
           GROUP BY p.id
           ORDER BY p.updated_at DESC""",
        (user_id,),
    )

    return [dict(row) for row in cursor.fetchall()]


def delete_playlist(
    playlist_id: str,
    user_id: str,
    db_path: str = "data/musicbot.db",
) -> bool:
    """Delete a playlist (owner only).

    Args:
        playlist_id: The playlist's UUID.
        user_id: Discord user ID (must be owner).
        db_path: Path to the SQLite database file.

    Returns:
        True if deleted, False if not found or unauthorized.
    """
    conn = get_connection(db_path)
    cursor = conn.cursor()

    # Check ownership
    cursor.execute(
        "SELECT user_id FROM playlists WHERE playlist_id = ?",
        (playlist_id,),
    )
    row = cursor.fetchone()
    if not row or row["user_id"] != user_id:
        logger.warning("User %s not authorized to delete playlist %s", user_id, playlist_id)
        return False

    # Delete tracks first (cascade should handle this, but be explicit)
    cursor.execute("DELETE FROM playlist_tracks WHERE playlist_id = ?", (playlist_id,))
    cursor.execute("DELETE FROM playlists WHERE playlist_id = ?", (playlist_id,))
    conn.commit()

    logger.info("Deleted playlist %s by user %s", playlist_id, user_id)
    return True


def get_max_tracks() -> int:
    """Get the maximum number of tracks allowed per playlist.

    Returns:
        Maximum tracks per playlist.
    """
    return _MAX_TRACKS_PER_PLAYLIST