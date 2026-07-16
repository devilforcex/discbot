"""Playlist CRUD operations."""

from __future__ import annotations

import logging
import uuid

from bot.database.database import get_connection

logger = logging.getLogger(__name__)


def create_playlist(
    user_id: str, guild_id: str, name: str, description: str = "", db_path: str = "data/musicbot.db"
) -> str | None:
    conn = get_connection(db_path)
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM playlists WHERE user_id = ? AND name = ?", (user_id, name))
    if cur.fetchone():
        logger.warning("Playlist '%s' already exists for user %s", name, user_id)
        return None
    playlist_id = str(uuid.uuid4())
    cur.execute(
        """INSERT INTO playlists (playlist_id, user_id, guild_id, name, description)
           VALUES (?, ?, ?, ?, ?)""",
        (playlist_id, user_id, guild_id, name, description),
    )
    conn.commit()
    logger.info("Created playlist '%s' (%s) for user %s", name, playlist_id, user_id)
    return playlist_id


def get_playlist(playlist_id: str, db_path: str = "data/musicbot.db") -> dict | None:
    conn = get_connection(db_path)
    cur = conn.cursor()
    cur.execute("SELECT * FROM playlists WHERE playlist_id = ?", (playlist_id,))
    row = cur.fetchone()
    if not row:
        return None
    playlist = dict(row)
    cur.execute(
        """SELECT * FROM playlist_tracks WHERE playlist_id = ? ORDER BY position ASC""",
        (playlist_id,),
    )
    playlist["tracks"] = [dict(r) for r in cur.fetchall()]
    playlist["track_count"] = len(playlist["tracks"])
    return playlist


def list_user_playlists(user_id: str, db_path: str = "data/musicbot.db") -> list[dict]:
    conn = get_connection(db_path)
    cur = conn.cursor()
    cur.execute(
        """SELECT p.*, COUNT(pt.id) as track_count
           FROM playlists p LEFT JOIN playlist_tracks pt ON p.playlist_id = pt.playlist_id
           WHERE p.user_id = ? GROUP BY p.id ORDER BY p.updated_at DESC""",
        (user_id,),
    )
    return [dict(row) for row in cur.fetchall()]


def delete_playlist(playlist_id: str, user_id: str, db_path: str = "data/musicbot.db") -> bool:
    conn = get_connection(db_path)
    cur = conn.cursor()
    cur.execute("SELECT user_id FROM playlists WHERE playlist_id = ?", (playlist_id,))
    row = cur.fetchone()
    if not row or row["user_id"] != user_id:
        logger.warning("User %s not authorized to delete playlist %s", user_id, playlist_id)
        return False
    cur.execute("DELETE FROM playlist_tracks WHERE playlist_id = ?", (playlist_id,))
    cur.execute("DELETE FROM playlists WHERE playlist_id = ?", (playlist_id,))
    conn.commit()
    logger.info("Deleted playlist %s by user %s", playlist_id, user_id)
    return True
