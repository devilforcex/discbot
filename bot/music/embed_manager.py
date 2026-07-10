"""
Rich embed builder for the Discord Music Bot — polished Nightmare / Boogie style.
"""

import math
from typing import Optional, Union

import discord

from bot.music.emoji import (
    COLOR_ERROR,
    COLOR_FAVORITE,
    COLOR_IDLE,
    COLOR_PAUSED,
    COLOR_PLAYING,
    COLOR_SUCCESS,
    EMOJI,
)
from bot.music.queue_manager import LoopMode


class EmbedManager:
    """Static methods for building rich Discord embeds."""

    # ------------------------------------------------------------
    # Now playing / Player
    # ------------------------------------------------------------

    @staticmethod
    def now_playing(
        title: str,
        author: str,
        uri: str,
        length: int,
        position: int = 0,
        thumbnail_url: Optional[str] = None,
        requester: Optional[str] = None,
        volume: int = 50,
        paused: bool = False,
        loop: Optional[Union[LoopMode, str]] = None,
        autoplay: bool = False,
        queue_len: int = 0,
        active_filter: str = "off",
    ) -> discord.Embed:
        return EmbedManager.player_now_playing_embed(
            title=title,
            author=author,
            uri=uri,
            length=length,
            position=position,
            thumbnail_url=thumbnail_url,
            requester=requester,
            volume=volume,
            paused=paused,
            loop=loop,
            autoplay=autoplay,
            queue_len=queue_len,
            active_filter=active_filter,
        )

    @staticmethod
    def player_now_playing_embed(
        title: str,
        author: str,
        uri: str,
        length: int,
        position: int = 0,
        thumbnail_url: Optional[str] = None,
        requester: Optional[str] = None,
        volume: int = 50,
        paused: bool = False,
        loop: Optional[Union[LoopMode, str]] = None,
        autoplay: bool = False,
        queue_len: int = 0,
        active_filter: str = "off",
    ) -> discord.Embed:
        """Full player embed used by the persistent player message — Boogie + Nightmare style."""
        # Better progress bar: ━ filled + ● head + ─ empty
        progress = EmbedManager._build_progress_bar(position, length, bar_len=18)
        color = COLOR_PAUSED if paused else COLOR_PLAYING
        state_icon = EMOJI["pause"] if paused else EMOJI["play"]
        state_label = "Paused" if paused else "Now Playing"

        loop_mode = loop
        if isinstance(loop, str):
            try:
                loop_mode = LoopMode(loop.lower())
            except ValueError:
                loop_mode = LoopMode.NONE
        if loop_mode is None:
            loop_mode = LoopMode.NONE

        loop_icons = {
            LoopMode.NONE: EMOJI["loop_none"],
            LoopMode.TRACK: EMOJI["loop_track"],
            LoopMode.QUEUE: EMOJI["loop_queue"],
        }
        loop_icon = loop_icons.get(loop_mode, EMOJI["loop_none"])
        loop_label = loop_mode.value if isinstance(loop_mode, LoopMode) else str(loop_mode)

        # Status line: Playing · Loop · Volume · Queue · Autoplay · Filter
        status_parts = [
            f"{state_icon} **{state_label}**",
            f"{loop_icon} `{loop_label}`",
            f"{EMOJI['volume']} `{volume}%`",
            f"{EMOJI['queue']} `{queue_len}`",
        ]
        if autoplay:
            status_parts.append(f"{EMOJI['autoplay']} Autoplay")
        if active_filter and active_filter != "off":
            # Try to get friendly name
            try:
                from bot.music.audio_filters import FILTER_INFO

                finfo = FILTER_INFO.get(active_filter, {})
                fname = finfo.get("label", active_filter)
                femoji = finfo.get("emoji", "🎛️")
                status_parts.append(f"{femoji} `{fname}`")
            except Exception:
                status_parts.append(f"🎛️ `{active_filter}`")

        status = " · ".join(status_parts)

        # Boogie-inspired description: Title linked, author below, status below
        embed = discord.Embed(
            title=f"{EMOJI['music']} {state_label}",
            description=f"[**{title}**]({uri})\n*{author}*\n\n{status}",
            color=color,
        )

        # Progress field like screenshot: bar + times
        pos_str = EmbedManager._format_duration(position)
        len_str = EmbedManager._format_duration(length)
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

    @staticmethod
    def player_idle_embed(
        queue_len: int = 0,
        loop: Optional[Union[LoopMode, str]] = None,
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

    # ------------------------------------------------------------
    # Queue
    # ------------------------------------------------------------

    @staticmethod
    def queue_embed(
        queue: list[dict],
        current_track: Optional[dict] = None,
        page: int = 1,
        page_size: int = 10,
        guild_name: str = "Server",
    ) -> discord.Embed:
        total_tracks = len(queue) + (1 if current_track else 0)
        total_pages = max(1, math.ceil(len(queue) / page_size))
        # Total duration
        total_ms = sum(t.get("length", 0) for t in queue)
        if current_track:
            total_ms += current_track.get("length", 0)
        total_dur = EmbedManager._format_duration(total_ms) if total_ms else "0:00"

        embed = discord.Embed(
            title=f"{EMOJI['queue']} Queue — {guild_name}",
            description=f"**{total_tracks}** track(s) • Total: `{total_dur}` • Use ◀️▶️ to navigate",
            color=COLOR_PLAYING,
        )

        if current_track:
            cur_dur = EmbedManager._format_duration(current_track.get("length", 0))
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
                    duration = EmbedManager._format_duration(track.get("length", 0))
                    title = track.get("title", "Unknown")[:60]
                    author = track.get("author", "Unknown")[:40]
                    req_id = track.get("requester_id")
                    req = f"<@{req_id}>" if req_id else ""
                    # Cleaner single-line: 1. Title — Author [dur] • @user
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
            embed.add_field(name="Queue", value="The queue is empty. Add songs with `!play <song>`.", inline=False)

        if total_pages > 1:
            embed.set_footer(text=f"Page {page}/{total_pages} • {len(queue)} queued • {total_dur} total — Buttons below to navigate")
        else:
            embed.set_footer(text=f"{len(queue)} queued • {total_dur} total — Shuffle/Refresh buttons")

        return embed

    # ------------------------------------------------------------
    # Playlists / Favorites
    # ------------------------------------------------------------

    @staticmethod
    def playlist_embed(
        playlist: dict,
        page: int = 1,
        page_size: int = 15,
    ) -> discord.Embed:
        tracks = playlist.get("tracks", [])
        total_pages = max(1, math.ceil(len(tracks) / page_size))
        total_ms = sum(t.get("length", 0) for t in tracks)
        total_dur = EmbedManager._format_duration(total_ms)

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
                duration = EmbedManager._format_duration(t.get("length", 0))
                title = t.get("title", "Unknown")[:50]
                track_lines.append(f"`{t['position']}.` [**{title}**]({t['uri']}) `[{duration}]`")

            embed.add_field(
                name=f"Tracks (Page {page}/{total_pages}) — Select menu to play",
                value="\n".join(track_lines),
                inline=False,
            )

        embed.set_footer(text=f"Playlist ID: {playlist['playlist_id']} • Use dropdown + Play All")
        return embed

    @staticmethod
    def favorites_embed(
        favorites: list[dict],
        page: int = 1,
        total: int = 0,
        page_size: int = 10,
    ) -> discord.Embed:
        total_pages = max(1, math.ceil(total / page_size))
        total_ms = sum(f.get("length", 0) for f in favorites)
        # Note: favorites page only, but show approximate

        embed = discord.Embed(
            title="⭐ Your Favorites",
            description=f"**{total}** favorite track(s)" + (f" • Page {page}/{total_pages}" if total else "") + "\nSelect a track from the menu below to play.",
            color=COLOR_FAVORITE,
        )

        if favorites:
            start_idx = (page - 1) * page_size
            track_lines = []
            for i, fav in enumerate(favorites, start=start_idx + 1):
                duration = EmbedManager._format_duration(fav.get("length", 0))
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

    # ------------------------------------------------------------
    # Help
    # ------------------------------------------------------------

    @staticmethod
    def help_embed() -> discord.Embed:
        embed = discord.Embed(
            title=f"{EMOJI['music']} Music Bot Commands",
            description=(
                "Prefix: `!` · Aliases: `!p` `!np` `!q` `!vol` `!dc`\n"
                "Player has persistent buttons + filter dropdown + seek (+10/-10/Replay)."
            ),
            color=COLOR_PLAYING,
        )

        embed.add_field(
            name=f"{EMOJI['play']} Playback",
            value=(
                "`!play <query>` — Search (Top 5 select) / URL\n"
                "`!pause` / `!resume` — Pause/resume\n"
                "`!skip` — Skip track\n"
                "`!stop` — Stop & clear queue\n"
                "`!disconnect` (`!dc`) — Leave voice\n"
                "`!seek <seconds>` / `!forward` / `!rewind` / `!replay`"
            ),
            inline=True,
        )

        embed.add_field(
            name=f"{EMOJI['queue']} Queue",
            value=(
                "`!queue` (`!q`) — View queue (◀️▶️ buttons)\n"
                "`!nowplaying` (`!np`) — Player + buttons\n"
                "`!shuffle` — Shuffle queue\n"
                "`!loop <none|track|queue>`\n"
                "`!autoplay [on|off|toggle]`"
            ),
            inline=True,
        )

        embed.add_field(
            name="⚙️ Settings & utility",
            value=(
                "`!volume <0-100>` (`!vol`)\n"
                "`!ping` — Latency\n"
                "`!help` — This menu\n"
                "`!status` / `!whoami`"
            ),
            inline=True,
        )

        embed.add_field(
            name="🎛️ Filters (new)",
            value=(
                "`!filter <name>` — Apply audio filter\n"
                "`!filters` — List filters + select menu\n"
                "`!filter reset` — Clear filters\n"
                "Presets: `bassboost`, `nightcore`,\n"
                "`vaporwave`, `pop`, `8d`, `lofi`,\n"
                "`karaoke`, `tremolo`\n"
                "*Also in player dropdown*"
            ),
            inline=True,
        )

        embed.add_field(
            name=f"{EMOJI['favorite']} Favorites",
            value=(
                "`!favorite` — Save current track\n"
                "`!favorites [page]` — List + play via ⭐ menu\n"
                "*(select + ◀️▶️ pagination)*"
            ),
            inline=True,
        )

        embed.add_field(
            name="📀 Playlists",
            value=(
                "`!playlists` — Your playlists (📀 menu)\n"
                "`!playlist_show <id>` — View + play via menu\n"
                "`!playlist_create <name>`\n"
                "`!playlist_add <id>` / `remove`\n"
                "`!playlist_play <id>` — Queue all"
            ),
            inline=True,
        )

        embed.add_field(
            name="🔒 Owner",
            value=(
                "`!adduser` / `!removeuser` / `!listusers`\n"
                "`!approve` / `!deny` / `!pendingrequests`\n"
                "`!blacklist` / `!unblacklist`\n"
                "`!247 on|off`"
            ),
            inline=True,
        )

        embed.add_field(
            name="🎛️ Player components",
            value=(
                "**Dropdown Row 0:** Select A Filter To Apply.\n"
                f"**Row 1:** {EMOJI['play_pause']} pause/resume · {EMOJI['skip']} skip · "
                f"{EMOJI['stop']} stop · {EMOJI['shuffle']} shuffle · "
                f"{EMOJI['loop_queue']} loop\n"
                f"**Row 2:** {EMOJI['vol_down']}/{EMOJI['vol_up']} volume · "
                f"{EMOJI['favorite']} fav · {EMOJI['queue']} queue · "
                f"{EMOJI['disconnect']} disconnect\n"
                "**Row 3:** ⏮️ replay · ⏪ -10s · ⏩ +10s"
            ),
            inline=False,
        )

        embed.set_footer(text="DrusaBota • Made with ❤️ by Steel • Use dropdown to switch category • Discord link in buttons below")
        return embed

    # ------------------------------------------------------------
    # Search / track added
    # ------------------------------------------------------------

    @staticmethod
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

        # Thumbnail from first track if available
        first_art = getattr(tracks[0], "artwork_url", None) if tracks else None
        if first_art:
            embed.set_thumbnail(url=first_art)

        lines = []
        for idx, t in enumerate(tracks[:5], start=1):
            dur = EmbedManager._format_duration(getattr(t, "length", 0) or 0)
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

    @staticmethod
    def filter_embed(active_filter: str = "off") -> discord.Embed:
        from bot.music.audio_filters import FILTER_INFO, get_filter_choices

        embed = discord.Embed(
            title="🎛️ Audio Filters",
            description="Select a filter from the dropdown below to enhance audio.\n"
            f"**Active:** `{active_filter}`",
            color=COLOR_PLAYING,
        )

        for value, label, desc, emoji in get_filter_choices():
            active_mark = " **(active)**" if value == active_filter else ""
            embed.add_field(
                name=f"{emoji} {label}{active_mark}",
                value=f"`{value}` — {desc}",
                inline=True,
            )

        embed.set_footer(text="Filters use Lavalink — Reset to clear • Works only while playing")
        return embed

    @staticmethod
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
                value=EmbedManager._format_duration(duration),
                inline=True,
            )

        if thumbnail_url:
            embed.set_thumbnail(url=thumbnail_url)

        return embed

    # ------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------

    @staticmethod
    def _build_progress_bar(
        current: int,
        total: int,
        length: int = 18,
        bar_len: Optional[int] = None,
    ) -> str:
        """Build a text-based progress bar with dot indicator: ──●── style inspired by screenshot."""
        size = bar_len if bar_len is not None else length
        if total <= 0:
            return "─" * size

        # Ratio 0-1
        ratio = max(0.0, min(1.0, current / total)) if total else 0
        # Position of dot (0 .. size-1)
        dot_pos = min(size - 1, max(0, int(ratio * (size - 1))))

        # Use ─ for base, ● for head, ━ for filled before head maybe
        # Let's do: ━ for filled, ● dot, ─ for empty
        bar_chars = []
        for i in range(size):
            if i == dot_pos:
                bar_chars.append("●")
            elif i < dot_pos:
                bar_chars.append("━")
            else:
                bar_chars.append("─")
        return "".join(bar_chars)

    @staticmethod
    def _format_duration(milliseconds: int) -> str:
        if not milliseconds or milliseconds <= 0:
            return "0:00"
        total_seconds = milliseconds // 1000
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        if hours > 0:
            return f"{hours}:{minutes:02d}:{seconds:02d}"
        return f"{minutes}:{seconds:02d}"
