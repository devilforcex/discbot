"""
Playback service — shared play-or-queue logic used by commands and views.
"""
from __future__ import annotations

import logging
from typing import Tuple

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
) -> Tuple[bool, object, wavelink.Playable]:
    """
    Play track if idle, otherwise queue it.
    Returns (is_playing_now: bool, embed, track)
    """
    voice_channel, player = await ensure_voice_player(bot, guild_id, member)

    settings = guild_settings.get(str(guild_id), bot.config.database_path)
    vol = settings.get("volume", 50)
    try:
        await player.set_volume(vol)
    except Exception:
        pass

    if player.playing:
        pos = bot.queue_manager.add(
            guild_id,
            {
                "title": track.title,
                "author": track.author,
                "uri": track.uri,
                "identifier": track.identifier,
                "length": track.length,
                "artwork_url": getattr(track, "artwork_url", None),
            },
            member.id,
        )
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
        try:
            setattr(track, "requester_id", member.id)
        except Exception:
            pass
        await player.play(track)
        bot.queue_manager.add_history(
            guild_id,
            {
                "title": track.title,
                "author": track.author,
                "uri": track.uri,
                "identifier": track.identifier,
                "length": track.length,
                "requester_id": member.id,
            },
        )
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
