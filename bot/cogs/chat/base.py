"""Shared utilities for chat cog."""

from __future__ import annotations

import discord
from discord.ext import commands

from bot.config import get_config


def check_ai_enabled(ctx: commands.Context) -> bool:
    """Check if AI is enabled, send error if not."""
    config = get_config()
    if not config.ai_enabled:
        ctx.bot.loop.create_task(ctx.send("❌ AI chat is disabled. Set `AI_ENABLED=true` in `.env` to enable."))
        return False
    return True


async def check_ai_enabled_interaction(ctx: discord.ApplicationContext) -> bool:
    """Check if AI is enabled for slash commands."""
    config = get_config()
    if not config.ai_enabled:
        await ctx.respond("❌ AI chat is disabled. Set `AI_ENABLED=true` in `.env` to enable.", ephemeral=True)
        return False
    return True