"""Shared helpers for music cogs."""

from __future__ import annotations

import logging

import discord

from bot.core.errors import DifferentVoiceChannel, NotInVoiceChannel
from bot.database.database import get_connection
from bot.music.player import Player

logger = logging.getLogger(__name__)

ALLOWED_OUTSIDE_MUSIC_CHANNEL = {"help", "ping", "whoami", "requestaccess"}


def voice_check(ctx) -> tuple:
    """Legacy wrapper for _voice_check that raises."""
    if not ctx.author.voice or not ctx.author.voice.channel:
        raise NotInVoiceChannel()
    voice_channel = ctx.author.voice.channel
    bot = ctx.bot
    existing_player = discord.utils.get(bot.voice_clients, guild__id=ctx.guild.id)
    if existing_player:
        if existing_player.channel != voice_channel:
            raise DifferentVoiceChannel()
        return voice_channel, existing_player
    return voice_channel, None


def get_player_from_ctx(ctx) -> Player | None:
    return discord.utils.get(ctx.bot.voice_clients, guild__id=ctx.guild.id)  # type: ignore[return-value]


async def check_guild_and_channel(ctx, config) -> bool:
    """Check if command is used in the correct guild. Allows commands from any channel,
    but responses will be routed to the music channel."""
    if ctx.guild is None:
        await ctx.send("❌ Music commands can only be used inside the configured server.")
        return False
    if ctx.guild.id != config.guild_id:
        await ctx.send("❌ This bot is restricted to its configured server.")
        return False
    return True


def get_response_channel(ctx, config) -> discord.TextChannel | None:
    """Get the channel where bot responses should be sent.
    Returns the music channel, or the current channel if it's the music channel,
    or None if music channel not found."""
    if ctx.guild is None:
        return None
    music_channel = ctx.guild.get_channel(config.music_channel_id)
    if isinstance(music_channel, discord.TextChannel):
        return music_channel
    # Fallback to current channel if music channel not found or not a text channel
    return ctx.channel if isinstance(ctx.channel, discord.TextChannel) else None


class MusicCogMixin:
    """Mixin to provide response channel handling for music cogs."""

    async def _get_response_channel(self, ctx) -> discord.TextChannel | None:
        return get_response_channel(ctx, self.bot.config)

    async def _send_to_response(self, ctx, **kwargs) -> discord.Message | None:
        """Send a message to the music channel instead of the command channel."""
        channel = await self._get_response_channel(ctx)
        if channel is None:
            # Fallback to original channel
            return await ctx.send(**kwargs)
        return await channel.send(**kwargs)

    async def _send_embed_to_response(self, ctx, embed, **kwargs) -> discord.Message | None:
        """Send an embed to the music channel instead of the command channel."""
        return await self._send_to_response(ctx, embed=embed, **kwargs)


async def is_authorized(ctx, bot) -> bool:
    if ctx.author.id == bot.config.owner_id:
        return True
    user_id = str(ctx.author.id)
    try:
        conn = get_connection(bot.config.database_path)
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM blacklisted_users WHERE user_id = ?", (user_id,))
        if cursor.fetchone():
            await ctx.send("❌ You are blacklisted.")
            return False
        cursor.execute("SELECT 1 FROM approved_users WHERE user_id = ?", (user_id,))
        if cursor.fetchone():
            return True
    except Exception as e:
        logger.error("Authorization check failed for user %s: %s", user_id, e)
    await ctx.send("❌ You are not authorized to use this bot.")
    return False


def is_owner_check(ctx, bot) -> bool:
    return ctx.author.id == bot.config.owner_id
