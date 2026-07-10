"""Favorites & playlists embeds."""
from __future__ import annotations

import math

import discord

from bot.music.emoji import COLOR_FAVORITE, COLOR_PLAYING
from .common import format_duration


def playlist_embed(
    playlist: dict,
    page: int = 1,
    page_size: int = 15,
) -> discord.Embed:
    tracks = playlist.get("tracks", [])
    total_pages = max(1, math.ceil(len(tracks) / page_size))
    total_ms = sum(t.get("length", 0) for t in tracks)
    total_dur = format_duration(total_ms)

    embed = discord.Embed(
        title=f"📀 {playlist['name']}",
        description=(playlist.get("description", "") or "No description") + f"\n\n**{len(tracks)}** tracks • `{total_dur}` total",
        color=COLOR_PLAYING,
    )

    embed.add_field(name="Owner", value=f"<@{playlist['user_id']}>", inline=True)
    embed.add_field(name="Tracks", value=f"{len(tracks)} • {total_dur}", inline=True)

    if tracks:
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        page_tracks = tracks[start_idx:end_idx]

        track_lines = []
        for t in page_tracks:
            duration = format_duration(t.get("length", 0))
            title = t.get("title", "Unknown")[:50]
            track_lines.append(f"`{t['position']}.` [**{title}**]({t['uri']}) `[{duration}]`")

        embed.add_field(
            name=f"Tracks (Page {page}/{total_pages}) — Select menu to play",
            value="\n".join(track_lines),
            inline=False,
        )

    embed.set_footer(text=f"Playlist ID: {playlist['playlist_id']} • Use dropdown + Play All")
    return embed


def favorites_embed(
    favorites: list[dict],
    page: int = 1,
    total: int = 0,
    page_size: int = 10,
) -> discord.Embed:
    total_pages = max(1, math.ceil(total / page_size))

    embed = discord.Embed(
        title="⭐ Your Favorites",
        description=f"**{total}** favorite track(s)" + (f" • Page {page}/{total_pages}" if total else "") + "\nSelect a track from the menu below to play.",
        color=COLOR_FAVORITE,
    )

    if favorites:
        start_idx = (page - 1) * page_size
        track_lines = []
        for i, fav in enumerate(favorites, start=start_idx + 1):
            duration = format_duration(fav.get("length", 0))
            title = fav.get("title", "Unknown")[:60]
            author = fav.get("author", "Unknown")[:40]
            track_lines.append(f"`{i}.` [**{title}**]({fav['uri']}) — *{author}* `[{duration}]`")
        embed.add_field(
            name=f"Saved Tracks (Page {page}/{total_pages})",
            value="\n".join(track_lines),
            inline=False,
        )
    else:
        embed.description = "You have no favorites yet. Use `!favorite` while a track is playing."

    embed.set_footer(text=f"Page {page}/{total_pages} • Use ⭐ dropdown to play • ◀️▶️ to navigate")
    return embed
