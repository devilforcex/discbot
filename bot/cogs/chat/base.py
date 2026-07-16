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


async def check_ai_enabled_interaction(ctx) -> bool:
    """Check if AI is enabled for hybrid/slash commands."""
    config = get_config()
    if not config.ai_enabled:
        await ctx.send(
            "❌ AI chat is disabled. Set `AI_ENABLED=true` in `.env` to enable.",
            ephemeral=True,
        )
        return False
    return True


def split_message(text: str, max_length: int = 2000) -> list[str]:
    """Split a long message into chunks that fit within Discord's message limit.

    Tries to break at newlines first, then at word boundaries, then hard-wraps.
    """
    if len(text) <= max_length:
        return [text]

    chunks: list[str] = []
    remaining = text

    while remaining:
        if len(remaining) <= max_length:
            chunks.append(remaining)
            break

        slice_end = remaining.rfind("\n", 0, max_length)
        if slice_end == -1 or slice_end < max_length // 2:
            slice_end = remaining.rfind(" ", 0, max_length)
        if slice_end == -1 or slice_end < max_length // 2:
            slice_end = max_length

        chunks.append(remaining[:slice_end].rstrip())
        remaining = remaining[slice_end:].lstrip()

    return chunks