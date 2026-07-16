"""Playlist track operations."""

from __future__ import annotations

import logging

from bot.database.database import get_connection

logger = logging.getLogger(__name__)

_MAX_TRACKS_PER_PLAYLIST = 200


def add_track(
    playlist_id: str,
    title: str,
    author: str,
    uri: str,
    identifier: str,
    length: int,
    added_by: str,
    artwork_url: str | None = None,
    db_path: str = "data/musicbot.db",
) -> bool:
    conn = get_connection(db_path)
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM playlists WHERE playlist_id = ?", (playlist_id,))
    if not cur.fetchone():
        logger.warning("Playlist %s not found", playlist_id)
        return False
    cur.execute("SELECT COUNT(*) FROM playlist_tracks WHERE playlist_id = ?", (playlist_id,))
    count = cur.fetchone()[0]
    if count >= _MAX_TRACKS_PER_PLAYLIST:
        logger.warning("Playlist %s is full (%d)", playlist_id, count)
        return False
    next_pos = count + 1
    cur.execute(
        """INSERT INTO playlist_tracks (playlist_id, position, title, author, uri, identifier, length, artwork_url, added_by)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (playlist_id, next_pos, title, author, uri, identifier, length, artwork_url, added_by),
    )
    conn.commit()
    cur.execute(
        "UPDATE playlists SET updated_at = CURRENT_TIMESTAMP WHERE playlist_id = ?", (playlist_id,)
    )
    conn.commit()
    logger.info("Added track '%s' to playlist %s (pos %d)", title, playlist_id, next_pos)
    return True


def remove_track(
    playlist_id: str, position: int, user_id: str, db_path: str = "data/musicbot.db"
) -> bool:
    conn = get_connection(db_path)
    cur = conn.cursor()
    cur.execute("SELECT user_id FROM playlists WHERE playlist_id = ?", (playlist_id,))
    row = cur.fetchone()
    if not row or row["user_id"] != user_id:
        logger.warning("User %s not authorized to modify playlist %s", user_id, playlist_id)
        return False
    cur.execute(
        "DELETE FROM playlist_tracks WHERE playlist_id = ? AND position = ?",
        (playlist_id, position),
    )
    if cur.rowcount == 0:
        return False
    cur.execute(
        """UPDATE playlist_tracks SET position = position - 1 WHERE playlist_id = ? AND position > ?""",
        (playlist_id, position),
    )
    conn.commit()
    cur.execute(
        "UPDATE playlists SET updated_at = CURRENT_TIMESTAMP WHERE playlist_id = ?", (playlist_id,)
    )
    conn.commit()
    logger.info("Removed track at pos %d from playlist %s", position, playlist_id)
    return True


def get_max_tracks() -> int:
    return _MAX_TRACKS_PER_PLAYLIST
