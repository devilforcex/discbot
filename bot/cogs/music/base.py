"""Shared helpers for music cogs."""
from __future__ import annotations

import logging
from typing import Optional, Tuple

import discord

from bot.core.errors import DifferentVoiceChannel, NotInVoiceChannel, build_error_embed
from bot.core.services.auth import check_authorized, is_owner, resolve_user_id
from bot.core.services.voice import get_player
from bot.database.database import get_connection
from bot.music.emoji import EMOJI
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


def get_player_from_ctx(ctx) -> Optional[Player]:
    return discord.utils.get(ctx.bot.voice_clients, guild__id=ctx.guild.id)


async def check_guild_and_channel(ctx, config) -> bool:
    if ctx.guild is None:
        await ctx.send("❌ Music commands can only be used inside the configured server.")
        return False
    if ctx.guild.id != config.guild_id:
        await ctx.send("❌ This bot is restricted to its configured server.")
        return False
    command_name = ctx.command.name if ctx.command else ""
    if command_name in ALLOWED_OUTSIDE_MUSIC_CHANNEL:
        return True
    if ctx.channel.id != config.music_channel_id:
        await ctx.send("❌ Music commands may only be used in the designated music channel.")
        return False
    return True


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
