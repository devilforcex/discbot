"""Queue embed."""

from __future__ import annotations

import math

import discord

from bot.music.emoji import COLOR_PLAYING, EMOJI

from .common import format_duration


def queue_embed(
    queue: list[dict],
    current_track: dict | None = None,
    page: int = 1,
    page_size: int = 10,
    guild_name: str = "Server",
) -> discord.Embed:
    total_tracks = len(queue) + (1 if current_track else 0)
    total_pages = max(1, math.ceil(len(queue) / page_size))
    total_ms = sum(t.get("length", 0) for t in queue)
    if current_track:
        total_ms += current_track.get("length", 0)
    total_dur = format_duration(total_ms) if total_ms else "0:00"

    embed = discord.Embed(
        title=f"{EMOJI['queue']} Queue — {guild_name}",
        description=f"**{total_tracks}** track(s) • Total: `{total_dur}` • Use ◀️▶️ to navigate",
        color=COLOR_PLAYING,
    )

    if current_track:
        cur_dur = format_duration(current_track.get("length", 0))
        req = current_track.get("requester_id")
        req_str = f"<@{req}>" if req else "Unknown"
        embed.add_field(
            name="▶️ Now Playing",
            value=f"[**{current_track['title']}**]({current_track['uri']})\n"
            f"*{current_track.get('author','Unknown')}* — `{cur_dur}` • {req_str}",
            inline=False,
        )

    if queue:
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        page_queue = queue[start_idx:end_idx]

        if page_queue:
            queue_lines = []
            for i, track in enumerate(page_queue, start=start_idx + 1):
                duration = format_duration(track.get("length", 0))
                title = track.get("title", "Unknown")[:60]
                author = track.get("author", "Unknown")[:40]
                req_id = track.get("requester_id")
                req = f"<@{req_id}>" if req_id else ""
                line = f"`{i}.` [**{title}**]({track['uri']}) — *{author}* `[{duration}]`"
                if req:
                    line += f" • {req}"
                queue_lines.append(line)
            embed.add_field(
                name=f"⏭️ Up Next (Page {page}/{total_pages})",
                value="\n".join(queue_lines),
                inline=False,
            )
    else:
        embed.add_field(
            name="Queue", value="The queue is empty. Add songs with `!play <song>`.", inline=False
        )

    if total_pages > 1:
        embed.set_footer(
            text=f"Page {page}/{total_pages} • {len(queue)} queued • {total_dur} total — Buttons below to navigate"
        )
    else:
        embed.set_footer(text=f"{len(queue)} queued • {total_dur} total — Shuffle/Refresh buttons")

    return embed
