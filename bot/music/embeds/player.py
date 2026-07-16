"""Player embeds: now playing & idle."""

from __future__ import annotations

import discord

from bot.music.emoji import COLOR_IDLE, COLOR_PAUSED, COLOR_PLAYING, EMOJI
from bot.music.queue_manager import LoopMode

from .common import build_progress_bar, format_duration


def player_now_playing_embed(
    title: str,
    author: str,
    uri: str,
    length: int,
    position: int = 0,
    thumbnail_url: str | None = None,
    requester: str | None = None,
    volume: int = 50,
    paused: bool = False,
    loop: LoopMode | str | None = None,
    autoplay: bool = False,
    queue_len: int = 0,
    active_filter: str = "off",
) -> discord.Embed:
    progress = build_progress_bar(position, length, bar_len=18)
    color = COLOR_PAUSED if paused else COLOR_PLAYING
    state_icon = EMOJI["pause"] if paused else EMOJI["play"]
    state_label = "Paused" if paused else "Now Playing"

    loop_mode: LoopMode = LoopMode.NONE
    if isinstance(loop, str):
        try:
            loop_mode = LoopMode(loop.lower())
        except ValueError:
            loop_mode = LoopMode.NONE
    elif isinstance(loop, LoopMode):
        loop_mode = loop

    loop_icons = {
        LoopMode.NONE: EMOJI["loop_none"],
        LoopMode.TRACK: EMOJI["loop_track"],
        LoopMode.QUEUE: EMOJI["loop_queue"],
    }
    loop_icon = loop_icons.get(loop_mode, EMOJI["loop_none"])
    loop_label = loop_mode.value

    status_parts = [
        f"{state_icon} **{state_label}**",
        f"{loop_icon} `{loop_label}`",
        f"{EMOJI['volume']} `{volume}%`",
        f"{EMOJI['queue']} `{queue_len}`",
    ]
    if autoplay:
        status_parts.append(f"{EMOJI['autoplay']} Autoplay")
    if active_filter and active_filter != "off":
        try:
            from bot.music.audio_filters import FILTER_INFO

            finfo = FILTER_INFO.get(active_filter, {})
            fname = finfo.get("label", active_filter)
            femoji = finfo.get("emoji", "🎛️")
            status_parts.append(f"{femoji} `{fname}`")
        except Exception:
            status_parts.append(f"🎛️ `{active_filter}`")

    status = " · ".join(status_parts)

    embed = discord.Embed(
        title=f"{EMOJI['music']} {state_label}",
        description=f"[**{title}**]({uri})\n*{author}*\n\n{status}",
        color=color,
    )

    pos_str = format_duration(position)
    len_str = format_duration(length)
    embed.add_field(
        name="Progress",
        value=f"`{progress}`\n`{pos_str}` / `{len_str}`",
        inline=False,
    )

    if thumbnail_url:
        embed.set_thumbnail(url=thumbnail_url)

    footer = "Use the buttons below to control playback • Filter in dropdown"
    if requester:
        footer = f"Requested by {requester} · {footer}"
    embed.set_footer(text=footer)
    return embed


def player_idle_embed(
    queue_len: int = 0,
    loop: LoopMode | str | None = None,
) -> discord.Embed:
    loop_label = "none"
    if isinstance(loop, LoopMode):
        loop_label = loop.value
    elif isinstance(loop, str):
        loop_label = loop

    embed = discord.Embed(
        title=f"{EMOJI['idle']} Nothing Playing",
        description=(
            f"Queue is empty — use `!play <song>` to start.\n\n"
            f"{EMOJI['queue']} Queue: `{queue_len}` · "
            f"{EMOJI['loop_none']} Loop: `{loop_label}`\n"
            f"🎛️ Filter: `off` — use filter dropdown when playing"
        ),
        color=COLOR_IDLE,
    )
    embed.set_footer(text="Player controls appear once music starts • !help for commands")
    return embed
