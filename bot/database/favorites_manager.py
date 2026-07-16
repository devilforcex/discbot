"""
Favorites database operations for the Discord Music Bot.
Provides functions to add, remove, list, and check favorite tracks.
"""

import logging

from bot.database.database import get_connection

logger = logging.getLogger(__name__)

_PAGE_SIZE = 20


def add_favorite(
    user_id: str,
    title: str,
    author: str,
    uri: str,
    identifier: str,
    length: int,
    artwork_url: str | None = None,
    db_path: str = "data/musicbot.db",
) -> bool:
    """Add a track to a user's favorites.

    Args:
        user_id: Discord user ID.
        title: Track title.
        author: Track author/artist.
        uri: Track URL.
        identifier: Track identifier.
        length: Duration in milliseconds.
        artwork_url: Optional thumbnail URL.
        db_path: Path to the SQLite database file.

    Returns:
        True if added, False if already exists.
    """
    conn = get_connection(db_path)
    cursor = conn.cursor()

    try:
        cursor.execute(
            """INSERT INTO user_favorites (user_id, title, author, uri, identifier, length, artwork_url)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (user_id, title, author, uri, identifier, length, artwork_url),
        )
        conn.commit()
        logger.info("Added favorite for user %s: %s", user_id, title)
        return True
    except Exception:
        # Duplicate entry (UNIQUE constraint)
        logger.debug("Favorite already exists for user %s: %s", user_id, identifier)
        return False


def remove_favorite(
    user_id: str,
    identifier: str,
    db_path: str = "data/musicbot.db",
) -> bool:
    """Remove a track from a user's favorites.

    Args:
        user_id: Discord user ID.
        identifier: Track identifier to remove.
        db_path: Path to the SQLite database file.

    Returns:
        True if removed, False if not found.
    """
    conn = get_connection(db_path)
    cursor = conn.cursor()

    cursor.execute(
        "DELETE FROM user_favorites WHERE user_id = ? AND identifier = ?",
        (user_id, identifier),
    )
    conn.commit()
    removed = cursor.rowcount > 0
    if removed:
        logger.info("Removed favorite for user %s: %s", user_id, identifier)
    return removed


def get_favorites(
    user_id: str,
    page: int = 1,
    page_size: int = _PAGE_SIZE,
    db_path: str = "data/musicbot.db",
) -> tuple[list[dict], int]:
    """Get paginated favorites for a user.

    Args:
        user_id: Discord user ID.
        page: Page number (1-indexed).
        page_size: Number of items per page.
        db_path: Path to the SQLite database file.

    Returns:
        Tuple of (list of favorite dicts, total count).
    """
    conn = get_connection(db_path)
    cursor = conn.cursor()

    # Get total count
    cursor.execute(
        "SELECT COUNT(*) FROM user_favorites WHERE user_id = ?",
        (user_id,),
    )
    total = cursor.fetchone()[0]

    # Get paginated results
    offset = (page - 1) * page_size
    cursor.execute(
        """SELECT * FROM user_favorites
           WHERE user_id = ?
           ORDER BY added_at DESC
           LIMIT ? OFFSET ?""",
        (user_id, page_size, offset),
    )

    favorites = [dict(row) for row in cursor.fetchall()]
    return favorites, total


def is_favorite(
    user_id: str,
    identifier: str,
    db_path: str = "data/musicbot.db",
) -> bool:
    """Check if a track is in a user's favorites.

    Args:
        user_id: Discord user ID.
        identifier: Track identifier.
        db_path: Path to the SQLite database file.

    Returns:
        True if the track is favorited.
    """
    conn = get_connection(db_path)
    cursor = conn.cursor()

    cursor.execute(
        "SELECT 1 FROM user_favorites WHERE user_id = ? AND identifier = ?",
        (user_id, identifier),
    )
    return cursor.fetchone() is not None


def get_favorite_count(
    user_id: str,
    db_path: str = "data/musicbot.db",
) -> int:
    """Get total number of favorites for a user.

    Args:
        user_id: Discord user ID.
        db_path: Path to the SQLite database file.

    Returns:
        Number of favorite tracks.
    """
    conn = get_connection(db_path)
    cursor = conn.cursor()

    cursor.execute(
        "SELECT COUNT(*) FROM user_favorites WHERE user_id = ?",
        (user_id,),
    )
    return cursor.fetchone()[0]
