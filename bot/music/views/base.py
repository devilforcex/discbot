"""Shared helpers for all interactive views — single source of truth."""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from bot.core.services.auth import check_authorized_sync_from_bot
from bot.core.services.voice import ensure_voice_player
from bot.core.services.playback import play_or_queue_track

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    import wavelink
    import discord


def is_url(query: str) -> bool:
    q = query.strip().lower()
    return (
        q.startswith("http://")
        or q.startswith("https://")
        or "youtube.com" in q
        or "youtu.be" in q
        or "spotify.com" in q
        or "soundcloud.com" in q
        or "music.youtube" in q
    )


def auth_ok(bot, user_id: int) -> tuple[bool, str]:
    """Backwards compat wrapper for old _auth_ok signature."""
    return check_authorized_sync_from_bot(bot, user_id)


async def ensure_voice_player_shared(bot, guild_id: int, member):
    return await ensure_voice_player(bot, guild_id, member)


async def play_wavelink_track_shared(bot, guild_id: int, member, track):
    """Wrapper around playback service to keep view logic clean."""
    return await play_or_queue_track(bot, guild_id, member, track)


# Legacy aliases — old code imported _is_url, _auth_ok etc.
_is_url = is_url
_auth_ok = auth_ok
_ensure_voice_player = ensure_voice_player_shared
_play_wavelink_track = play_wavelink_track_shared
