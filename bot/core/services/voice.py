"""
Voice service — single place for voice channel checks.
"""

from __future__ import annotations

import logging

import discord

from bot.core.errors import DifferentVoiceChannel, NotInVoiceChannel
from bot.music.emoji import EMOJI

logger = logging.getLogger(__name__)


def get_player(bot, guild_id: int):
    """Get existing voice client for guild."""
    return discord.utils.get(bot.voice_clients, guild__id=guild_id)


def voice_check(member: discord.Member, existing_player) -> str | None:
    """
    Validate member voice state vs bot player.
    Returns error message or None if OK.
    """
    voice_state = getattr(member, "voice", None)
    voice_channel = getattr(voice_state, "channel", None)
    if not voice_channel:
        return f"{EMOJI['error']} You must be in a voice channel."
    if existing_player and existing_player.channel and voice_channel != existing_player.channel:
        return f"{EMOJI['error']} You must be in the same voice channel as the bot."
    return None


def voice_check_or_raise(
    member: discord.Member, existing_player
) -> tuple[discord.VoiceChannel, object]:
    """Raises NotInVoiceChannel / DifferentVoiceChannel on failure."""
    voice_state = getattr(member, "voice", None)
    channel = getattr(voice_state, "channel", None)
    if not channel:
        raise NotInVoiceChannel()
    if existing_player and existing_player.channel != channel:
        raise DifferentVoiceChannel()
    return channel, existing_player


async def ensure_voice_player(bot, guild_id: int, member: discord.Member):
    """
    Ensure member in voice and return (voice_channel, player).
    Creates player via Lavalink client if needed.
    """
    voice_state = getattr(member, "voice", None)
    if not voice_state or not voice_state.channel:
        raise ValueError(f"{EMOJI['error']} You must be in a voice channel.")
    voice_channel = voice_state.channel
    existing = get_player(bot, guild_id)
    if existing and existing.channel != voice_channel:
        raise ValueError(f"{EMOJI['error']} You must be in the same voice channel as the bot.")
    if existing:
        return voice_channel, existing
    player = await bot.lavalink.get_player(guild_id, voice_channel)
    return voice_channel, player
