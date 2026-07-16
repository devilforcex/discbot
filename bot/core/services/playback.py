"""
Playback service — shared play-or-queue logic used by commands and views.
"""

from __future__ import annotations

import contextlib
import logging

import discord
import wavelink

from bot.core.services.voice import ensure_voice_player
from bot.database import guild_settings
from bot.music.embed_manager import EmbedManager

logger = logging.getLogger(__name__)


async def play_or_queue_track(
    bot,
    guild_id: int,
    member,
    track: wavelink.Playable,
) -> tuple[bool, discord.Embed, wavelink.Playable]:
    """
    Play track if idle, otherwise queue it.
    Returns (is_playing_now: bool, embed, track)
    """
    _, player = await ensure_voice_player(bot, guild_id, member)

    settings = guild_settings.get(str(guild_id), bot.config.database_path)
    vol = settings.get("volume", 50)
    with contextlib.suppress(Exception):
        await player.set_volume(vol)

    if player.playing:
        pos = bot.queue_manager.add(guild_id, track, member.id)
        embed = EmbedManager.track_added(
            title=track.title,
            uri=track.uri,
            position=pos,
            queue_length=bot.queue_manager.get_length(guild_id),
            duration=track.length,
        )
        if hasattr(bot, "player_messages"):
            try:
                await bot.player_messages.update_now_playing(guild_id)
            except Exception as e:
                logger.debug("player_messages update failed: %s", e)
        return False, embed, track
    else:
        if hasattr(player, "store_track"):
            player.store_track(track)
        with contextlib.suppress(Exception):
            track.requester_id = member.id
        await player.play(track)
        bot.queue_manager.add_history(guild_id, track)
        if hasattr(bot, "player_messages"):
            try:
                await bot.player_messages.update_now_playing(guild_id)
            except Exception as e:
                logger.debug("player_messages update failed: %s", e)
        embed = EmbedManager.now_playing(
            title=track.title,
            author=track.author,
            uri=track.uri,
            length=track.length,
            thumbnail_url=getattr(track, "artwork_url", None),
            requester=member.mention,
            volume=vol,
        )
        return True, embed, track
