"""
Rich embed builder for the Discord Music Bot.
Provides styled discord.Embed objects for all music-related features.
"""

import math
from typing import Optional

import discord


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
    ) -> discord.Embed:
        """Build a now-playing embed with progress bar.

        Args:
            title: Track title.
            author: Track author/artist.
            uri: Track URL.
            length: Track duration in milliseconds.
            position: Current playback position in milliseconds.
            thumbnail_url: Optional thumbnail URL.
            requester: Discord user mention who requested the track.
            volume: Current volume level.

        Returns:
            A styled now-playing embed.
        """
        # Calculate progress bar
        progress = EmbedManager._build_progress_bar(position, length, length=18)

        embed = discord.Embed(
            title="🎵 Now Playing",
            description=f"[**{title}**]({uri})",
            color=discord.Color.brand_green(),
        )

        embed.add_field(name="Artist", value=author, inline=True)
        embed.add_field(
            name="Duration",
            value=f"{EmbedManager._format_duration(position)} / {EmbedManager._format_duration(length)}",
            inline=True,
        )
        embed.add_field(name="Volume", value=f"{volume}%", inline=True)

        embed.add_field(
            name="Progress",
            value=f"`{progress}`",
            inline=False,
        )

        if thumbnail_url:
            embed.set_thumbnail(url=thumbnail_url)

        if requester:
            embed.set_footer(text=f"Requested by {requester}")

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
        """Build a comprehensive help embed with all commands.

        Returns:
            A styled help embed.
        """
        embed = discord.Embed(
            title="🎶 Music Bot Commands",
            description="Control music playback with these slash commands.",
            color=discord.Color.blurple(),
        )

        # Playback commands
        embed.add_field(
            name="▶️ Playback",
            value=(
                "`/play` — Search and play music\n"
                "`/pause` — Pause playback\n"
                "`/resume` — Resume playback\n"
                "`/skip` — Skip current track\n"
                "`/stop` — Stop playback\n"
                "`/disconnect` — Disconnect from voice"
            ),
            inline=True,
        )

        # Queue commands
        embed.add_field(
            name="📋 Queue",
            value=(
                "`/queue` — View the queue\n"
                "`/nowplaying` — Show current track\n"
                "`/shuffle` — Shuffle the queue\n"
                "`/loop` — Set loop mode\n"
                "`/autoplay` — Toggle autoplay"
            ),
            inline=True,
        )

        # Settings commands
        embed.add_field(
            name="⚙️ Settings",
            value=(
                "`/volume` — Set volume (0-100)\n"
                "`/ping` — Check latency\n"
                "`/help` — Show this help"
            ),
            inline=True,
        )

        # Favorites commands
        embed.add_field(
            name="⭐ Favorites",
            value=(
                "`/favorite` — Save current track\n"
                "`/favorites` — List your favorites"
            ),
            inline=True,
        )

        # Playlist commands
        embed.add_field(
            name="📀 Playlists",
            value=(
                "`/playlist-create` — Create a playlist\n"
                "`/playlist-add` — Add current track\n"
                "`/playlist-remove` — Remove track\n"
                "`/playlist-play` — Play a playlist"
            ),
            inline=True,
        )

        embed.set_footer(text="Use / before each command")
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
            title="✅ Added to Queue",
            description=f"[**{title}**]({uri})",
            color=discord.Color.green(),
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
    ) -> str:
        """Build a text-based progress bar.

        Args:
            current: Current position in milliseconds.
            total: Total length in milliseconds.
            length: Total characters in the bar.

        Returns:
            A string progress bar like '████████░░░░░░░░░░'.
        """
        if total <= 0:
            return "░" * length

        progress_ratio = current / total
        filled = min(length, max(0, round(progress_ratio * length)))
        empty = length - filled
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