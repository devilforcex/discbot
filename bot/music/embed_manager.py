"""
Rich embed builder for the Discord Music Bot.
Provides styled discord.Embed objects for all music-related features.
"""

import math
from typing import Optional, Union

import discord

from bot.music.emoji import (
    COLOR_ERROR,
    COLOR_FAVORITE,
    COLOR_IDLE,
    COLOR_INFO,
    COLOR_PAUSED,
    COLOR_PLAYING,
    COLOR_SUCCESS,
    EMOJI,
)
from bot.music.queue_manager import LoopMode


class EmbedManager:
    """Static methods for building rich Discord embeds."""

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
    ) -> discord.Embed:
        """Build a now-playing embed with progress bar."""
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
    ) -> discord.Embed:
        """Full player embed used by the persistent player message."""
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

        status = (
            f"{state_icon} **{state_label}** · "
            f"{loop_icon} `{loop_label}` · "
            f"{EMOJI['volume']} `{volume}%` · "
            f"{EMOJI['queue']} `{queue_len}`"
        )
        if autoplay:
            status += f" · {EMOJI['autoplay']} Autoplay"

        embed = discord.Embed(
            title=f"{EMOJI['music']} {state_label}",
            description=f"[**{title}**]({uri})\n*{author}*\n\n{status}",
            color=color,
        )
        embed.add_field(
            name="Progress",
            value=(
                f"`{progress}`\n"
                f"`{EmbedManager._format_duration(position)}` / "
                f"`{EmbedManager._format_duration(length)}`"
            ),
            inline=False,
        )

        if thumbnail_url:
            embed.set_thumbnail(url=thumbnail_url)

        footer = "Use the buttons below to control playback"
        if requester:
            footer = f"Requested by {requester} · {footer}"
        embed.set_footer(text=footer)
        return embed

    @staticmethod
    def player_idle_embed(
        queue_len: int = 0,
        loop: Optional[Union[LoopMode, str]] = None,
    ) -> discord.Embed:
        """Idle state for the persistent player message."""
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
                f"{EMOJI['loop_none']} Loop: `{loop_label}`"
            ),
            color=COLOR_IDLE,
        )
        embed.set_footer(text="Player buttons work once a track is playing")
        return embed

    @staticmethod
    def queue_embed(
        queue: list[dict],
        current_track: Optional[dict] = None,
        page: int = 1,
        page_size: int = 10,
        guild_name: str = "Server",
    ) -> discord.Embed:
        """Build a paginated queue display embed.

        Args:
            queue: List of queued track dicts.
            current_track: Currently playing track dict (optional).
            page: Current page number.
            page_size: Items per page.
            guild_name: Guild name for the embed title.

        Returns:
            A styled queue embed.
        """
        total_tracks = len(queue) + (1 if current_track else 0)
        total_pages = max(1, math.ceil(len(queue) / page_size))

        embed = discord.Embed(
            title=f"📋 Queue — {guild_name}",
            description=f"**{total_tracks}** track(s) in queue",
            color=discord.Color.blue(),
        )

        # Currently playing
        if current_track:
            embed.add_field(
                name="▶️ Now Playing",
                value=f"[**{current_track['title']}**]({current_track['uri']})\n"
                      f"Requested by <@{current_track.get('requester_id', 'unknown')}>",
                inline=False,
            )

        # Queued tracks
        if queue:
            start_idx = (page - 1) * page_size
            end_idx = start_idx + page_size
            page_queue = queue[start_idx:end_idx]

            if page_queue:
                queue_lines = []
                for i, track in enumerate(page_queue, start=start_idx + 1):
                    duration = EmbedManager._format_duration(track.get("length", 0))
                    queue_lines.append(
                        f"`{i}.` [**{track['title']}**]({track['uri']}) — `{duration}`\n"
                        f"└ Requested by <@{track.get('requester_id', 'unknown')}>"
                    )
                embed.add_field(
                    name=f"⏭️ Up Next (Page {page}/{total_pages})",
                    value="\n".join(queue_lines),
                    inline=False,
                )
        else:
            embed.add_field(name="Queue", value="The queue is empty.", inline=False)

        if total_pages > 1:
            embed.set_footer(text=f"Page {page}/{total_pages} • {len(queue)} queued tracks")

        return embed

    @staticmethod
    def playlist_embed(
        playlist: dict,
        page: int = 1,
        page_size: int = 15,
    ) -> discord.Embed:
        """Build a playlist detail embed.

        Args:
            playlist: Playlist dict with tracks list.
            page: Current page number.
            page_size: Items per page.

        Returns:
            A styled playlist embed.
        """
        tracks = playlist.get("tracks", [])
        total_pages = max(1, math.ceil(len(tracks) / page_size))

        embed = discord.Embed(
            title=f"📀 {playlist['name']}",
            description=playlist.get("description", "") or "No description",
            color=discord.Color.purple(),
        )

        embed.add_field(name="Owner", value=f"<@{playlist['user_id']}>", inline=True)
        embed.add_field(name="Tracks", value=str(len(tracks)), inline=True)

        if tracks:
            start_idx = (page - 1) * page_size
            end_idx = start_idx + page_size
            page_tracks = tracks[start_idx:end_idx]

            track_lines = []
            for t in page_tracks:
                duration = EmbedManager._format_duration(t.get("length", 0))
                track_lines.append(
                    f"`{t['position']}.` [**{t['title']}**]({t['uri']}) — `{duration}`"
                )

            embed.add_field(
                name=f"Tracks (Page {page}/{total_pages})",
                value="\n".join(track_lines),
                inline=False,
            )

        embed.set_footer(text=f"Playlist ID: {playlist['playlist_id']}")
        return embed

    @staticmethod
    def favorites_embed(
        favorites: list[dict],
        page: int = 1,
        total: int = 0,
        page_size: int = 10,
    ) -> discord.Embed:
        """Build a favorites list embed.

        Args:
            favorites: List of favorite track dicts.
            page: Current page number.
            total: Total number of favorites.
            page_size: Items per page.

        Returns:
            A styled favorites embed.
        """
        total_pages = max(1, math.ceil(total / page_size))

        embed = discord.Embed(
            title="⭐ Your Favorites",
            description=f"**{total}** favorite track(s)" if total else "You have no favorites yet.",
            color=discord.Color.gold(),
        )

        if favorites:
            start_idx = (page - 1) * page_size
            track_lines = []
            for i, fav in enumerate(favorites, start=start_idx + 1):
                duration = EmbedManager._format_duration(fav.get("length", 0))
                track_lines.append(
                    f"`{i}.` [**{fav['title']}**]({fav['uri']}) — `{duration}`\n"
                    f"└ {fav['author']}"
                )
            embed.add_field(
                name=f"Saved Tracks (Page {page}/{total_pages})",
                value="\n".join(track_lines),
                inline=False,
            )

        if total_pages > 1:
            embed.set_footer(text=f"Page {page}/{total_pages}")

        return embed

    @staticmethod
    def help_embed() -> discord.Embed:
        """Build a comprehensive help embed with all commands."""
        embed = discord.Embed(
            title=f"{EMOJI['music']} Music Bot Commands",
            description=(
                "Prefix: `!` · Aliases: `!p` `!np` `!q` `!vol` `!dc`\n"
                "Player buttons on the Now Playing message also control playback."
            ),
            color=COLOR_PLAYING,
        )

        embed.add_field(
            name=f"{EMOJI['play']} Playback",
            value=(
                "`!play <query>` — Search (+ select menu) / URL\n"
                "`!pause` / `!resume` — Pause or resume\n"
                "`!skip` — Skip track\n"
                "`!stop` — Stop & clear queue\n"
                "`!disconnect` (`!dc`) — Leave voice"
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
            name="🎛️ Player buttons",
            value=(
                f"{EMOJI['play_pause']} pause/resume · {EMOJI['skip']} skip · "
                f"{EMOJI['stop']} stop · {EMOJI['shuffle']} shuffle · "
                f"{EMOJI['loop_queue']} loop cycle\n"
                f"{EMOJI['vol_down']}/{EMOJI['vol_up']} volume · "
                f"{EMOJI['favorite']} favorite · {EMOJI['queue']} queue · "
                f"{EMOJI['disconnect']} disconnect"
            ),
            inline=False,
        )

        embed.set_footer(text="Music commands work in the designated music channel")
        return embed

    @staticmethod
    def search_results_embed(query: str, tracks: list) -> discord.Embed:
        """Build an embed for track selection (top 5 results)."""
        embed = discord.Embed(
            title=f"{EMOJI['music']} Search results for: {query[:100]}",
            description="Select a track from the menu below. Only the requester can pick.",
            color=COLOR_PLAYING,
        )
        if not tracks:
            embed.description = f"No results for **{query}**."
            embed.color = COLOR_ERROR
            return embed

        lines = []
        for idx, t in enumerate(tracks[:5], start=1):
            dur = EmbedManager._format_duration(getattr(t, "length", 0) or 0)
            title = getattr(t, "title", "Unknown")
            author = getattr(t, "author", "Unknown")
            uri = getattr(t, "uri", "")
            # Markdown link
            lines.append(f"`{idx}.` [**{title}**]({uri}) — *{author}* `[{dur}]`")

        embed.add_field(
            name=f"Top {min(5, len(tracks))} tracks",
            value="\n".join(lines) if lines else "No tracks",
            inline=False,
        )
        embed.set_footer(text="Pick from the dropdown • 60s timeout")
        return embed

    @staticmethod
    def track_added(
        title: str,
        uri: str,
        position: int,
        queue_length: int,
        duration: Optional[int] = None,
    ) -> discord.Embed:
        """Build a track-added confirmation embed.

        Args:
            title: Track title.
            uri: Track URL.
            position: Position in queue.
            queue_length: Total tracks in queue.
            duration: Track duration in milliseconds (optional).

        Returns:
            A styled confirmation embed.
        """
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

        return embed

    @staticmethod
    def _build_progress_bar(
        current: int,
        total: int,
        length: int = 18,
        bar_len: Optional[int] = None,
    ) -> str:
        """Build a text-based progress bar like '████████░░░░░░░░░░'."""
        size = bar_len if bar_len is not None else length
        if total <= 0:
            return "░" * size

        progress_ratio = current / total
        filled = min(size, max(0, round(progress_ratio * size)))
        empty = size - filled
        return "█" * filled + "░" * empty

    @staticmethod
    def _format_duration(milliseconds: int) -> str:
        """Format milliseconds to a human-readable time string.

        Args:
            milliseconds: Duration in milliseconds.

        Returns:
            Formatted string like '3:45' or '1:02:15' for longer durations.
        """
        if not milliseconds or milliseconds <= 0:
            return "0:00"

        total_seconds = milliseconds // 1000
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60

        if hours > 0:
            return f"{hours}:{minutes:02d}:{seconds:02d}"
        return f"{minutes}:{seconds:02d}"