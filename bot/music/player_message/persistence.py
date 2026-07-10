"""Persistence for player message IDs."""
from __future__ import annotations

import logging
from typing import Optional

from bot.database.database import get_connection

logger = logging.getLogger(__name__)


class PlayerPersistence:
    def __init__(self, bot):
        self.bot = bot

    def _db_key(self, guild_id: int, kind: str) -> str:
        return f"player_{kind}_{guild_id}"

    def save_ids(self, guild_id: int, channel_id: int, message_id: int) -> None:
        try:
            conn = get_connection(self.bot.config.database_path)
            cur = conn.cursor()
            for key, value in (
                (self._db_key(guild_id, "channel"), str(channel_id)),
                (self._db_key(guild_id, "message"), str(message_id)),
            ):
                cur.execute(
                    """
                    INSERT INTO bot_settings (key, value) VALUES (?, ?)
                    ON CONFLICT(key) DO UPDATE SET value = excluded.value
                    """,
                    (key, value),
                )
            conn.commit()
        except Exception as e:
            logger.debug("Failed to save player message ids: %s", e)

    def load_ids(self, guild_id: int) -> tuple[Optional[int], Optional[int]]:
        try:
            conn = get_connection(self.bot.config.database_path)
            cur = conn.cursor()
            cur.execute("SELECT value FROM bot_settings WHERE key = ?", (self._db_key(guild_id, "channel"),))
            ch = cur.fetchone()
            cur.execute("SELECT value FROM bot_settings WHERE key = ?", (self._db_key(guild_id, "message"),))
            msg = cur.fetchone()
            channel_id = int(ch["value"]) if ch and ch["value"] else None
            message_id = int(msg["value"]) if msg and msg["value"] else None
            return channel_id, message_id
        except Exception as e:
            logger.debug("Failed to load player message ids: %s", e)
            return None, None

    def clear_ids(self, guild_id: int) -> None:
        try:
            conn = get_connection(self.bot.config.database_path)
            cur = conn.cursor()
            cur.execute(
                "DELETE FROM bot_settings WHERE key IN (?, ?)",
                (self._db_key(guild_id, "channel"), self._db_key(guild_id, "message")),
            )
            conn.commit()
        except Exception as e:
            logger.debug("Failed to clear player message ids: %s", e)
