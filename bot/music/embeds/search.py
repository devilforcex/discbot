"""Search & track added embeds."""
from __future__ import annotations

from typing import Optional

import discord

from bot.music.emoji import COLOR_ERROR, COLOR_PLAYING, COLOR_SUCCESS, EMOJI
from .common import format_duration


def search_results_embed(query: str, tracks: list) -> discord.Embed:
    embed = discord.Embed(
        title=f"{EMOJI['music']} Search results for: {query[:100]}",
        description="Select a track from the dropdown below. Only authorized users can pick.",
        color=COLOR_PLAYING,
    )
    if not tracks:
        embed.description = f"No results for **{query}**."
        embed.color = COLOR_ERROR
        return embed

    first_art = getattr(tracks[0], "artwork_url", None) if tracks else None
    if first_art:
        embed.set_thumbnail(url=first_art)

    lines = []
    for idx, t in enumerate(tracks[:5], start=1):
        dur = format_duration(getattr(t, "length", 0) or 0)
        title = getattr(t, "title", "Unknown")[:60]
        author = getattr(t, "author", "Unknown")[:50]
        uri = getattr(t, "uri", "")
        lines.append(f"`{idx}.` [**{title}**]({uri}) — *{author}* `[{dur}]`")

    embed.add_field(
        name=f"Top {min(5, len(tracks))} tracks — dropdown below",
        value="\n".join(lines) if lines else "No tracks",
        inline=False,
    )
    embed.set_footer(text="Pick from the dropdown • 60s timeout • URL skips search")
    return embed


def track_added(
    title: str,
    uri: str,
    position: int,
    queue_length: int,
    duration: Optional[int] = None,
    thumbnail_url: Optional[str] = None,
) -> discord.Embed:
    embed = discord.Embed(
        title=f"{EMOJI['ok']} Added to Queue",
        description=f"[**{title}**]({uri})",
        color=COLOR_SUCCESS,
    )

    embed.add_field(name="Position", value=f"#{position}", inline=True)
    embed.add_field(name="Queue", value=f"{queue_length} track(s)", inline=True)

    if duration:
        embed.add_field(
            name="Duration",
            value=format_duration(duration),
            inline=True,
        )

    if thumbnail_url:
        embed.set_thumbnail(url=thumbnail_url)

    return embed
