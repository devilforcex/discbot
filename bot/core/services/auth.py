"""
Centralized authentication service — single source of truth.

Replaces duplicated auth logic from admin_commands, music_commands,
player_controller and views._auth_ok.
"""

from __future__ import annotations

import logging

from bot.database.database import get_connection
from bot.music.emoji import EMOJI

logger = logging.getLogger(__name__)


def resolve_user_id(user_input: str) -> str | None:
    """
    Resolve Discord user ID from raw ID or mention.

    Supports:
    - 123456789012345678
    - <@123456789012345678>
    - <@!123456789012345678>
    """
    stripped = user_input.strip()
    if stripped.startswith("<@") and stripped.endswith(">"):
        inner = stripped[2:-1]
        if inner.startswith("!"):
            inner = inner[1:]
        return inner if inner.isdigit() else None
    return stripped if stripped.isdigit() else None


def is_owner(user_id: int, owner_id: int) -> bool:
    return user_id == owner_id


def check_authorized(user_id: int, owner_id: int, db_path: str) -> tuple[bool, str]:
    """
    Check if user is authorized.
    Returns (allowed, error_message).

    Order: owner > blacklist > whitelist > deny.
    """
    if is_owner(user_id, owner_id):
        return True, ""

    uid = str(user_id)
    try:
        conn = get_connection(db_path)
        cur = conn.cursor()
        cur.execute("SELECT 1 FROM blacklisted_users WHERE user_id = ?", (uid,))
        if cur.fetchone():
            return False, f"{EMOJI['error']} You are blacklisted."
        cur.execute("SELECT 1 FROM approved_users WHERE user_id = ?", (uid,))
        if cur.fetchone():
            return True, ""
    except Exception as e:
        logger.error("Auth check failed for %s: %s", uid, e)

    return False, f"{EMOJI['error']} You are not authorized to use this bot."


def check_authorized_sync_from_bot(bot, user_id: int) -> tuple[bool, str]:
    """Convenience wrapper that extracts owner_id and db_path from bot."""
    return check_authorized(user_id, bot.config.owner_id, bot.config.database_path)
