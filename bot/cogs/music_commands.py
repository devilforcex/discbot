"""
Music command cog for the Discord Music Bot.
Implements all prefix commands with Phase 2 interactive UI: search select, queue pagination, favorites, playlists.
"""

import logging
from typing import Optional

import discord
import wavelink
from discord.ext import commands

from bot.core.errors import (
    DifferentVoiceChannel,
    LavalinkNotConnected,
    NoPlayer,
    NotInVoiceChannel,
    NothingPlaying,
    QueueEmpty,
    TrackNotFound,
    build_error_embed,
)
from bot.database import favorites_manager, guild_settings, history_manager, playlist_manager
from bot.database.database import get_connection
from bot.music.embed_manager import EmbedManager
from bot.music.emoji import EMOJI
from bot.music.player import Player
from bot.music.queue_manager import LoopMode
from bot.music.views import (
    FavoritesPaginatorView,
    PlaylistDetailView,
    PlaylistListView,
    QueuePaginatorView,
    SearchView,
    _is_url,
)

logger = logging.getLogger(__name__)

ALLOWED_OUTSIDE_MUSIC_CHANNEL = {"help", "ping", "whoami", "requestaccess"}


def _voice_check(ctx: commands.Context) -> tuple:
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


def _get_player(ctx: commands.Context) -> Optional[Player]:
    return discord.utils.get(ctx.bot.voice_clients, guild__id=ctx.guild.id)


class MusicCommands(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # ============================================================
    # Authorization & Gatekeeping Helpers
    # ============================================================

    async def _check_guild_and_channel(self, ctx: commands.Context) -> bool:
        config = self.bot.config
        if ctx.guild.id != config.guild_id:
            return False
        command_name = ctx.command.name if ctx.command else ""
        if command_name in ALLOWED_OUTSIDE_MUSIC_CHANNEL:
            return True
        if ctx.channel.id != config.music_channel_id:
            await ctx.send("❌ Music commands may only be used in the designated music channel.")
            return False
        return True

    async def _is_authorized(self, ctx: commands.Context) -> bool:
        if ctx.author.id == self.bot.config.owner_id:
            return True
        user_id = str(ctx.author.id)
        try:
            conn = get_connection(self.bot.config.database_path)
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

    async def _require_authorized(self, ctx: commands.Context) -> bool:
        return await self._is_authorized(ctx)

    # ============================================================
    # Voice & Playback Helpers
    # ============================================================

    async def _ensure_voice(self, ctx: commands.Context) -> tuple:
        voice_channel, player = _voice_check(ctx)
        if player is None:
            player = await self.bot.lavalink.get_player(ctx.guild.id, voice_channel)
        return voice_channel, player

    async def _play_track(
        self,
        ctx: commands.Context,
        player: Player,
        track: wavelink.Playable,
    ) -> None:
        settings = guild_settings.get(str(ctx.guild.id), self.bot.config.database_path)
        await player.set_volume(settings.get("volume", 50))
        if player.playing:
            position = self.bot.queue_manager.add(
                ctx.guild.id,
                {
                    "title": track.title,
                    "author": track.author,
                    "uri": track.uri,
                    "identifier": track.identifier,
                    "length": track.length,
                    "artwork_url": getattr(track, "artwork_url", None),
                },
                ctx.author.id,
            )
            embed = EmbedManager.track_added(
                title=track.title,
                uri=track.uri,
                position=position,
                queue_length=self.bot.queue_manager.get_length(ctx.guild.id),
                duration=track.length,
            )
            await ctx.send(embed=embed, delete_after=10)
            if hasattr(self.bot, "player_messages"):
                await self.bot.player_messages.update_now_playing(ctx.guild.id)
        else:
            await player.play(track)
            self.bot.queue_manager.add_history(
                ctx.guild.id,
                {
                    "title": track.title,
                    "author": track.author,
                    "uri": track.uri,
                    "identifier": track.identifier,
                    "length": track.length,
                    "requester_id": ctx.author.id,
                },
            )
            if hasattr(self.bot, "player_messages"):
                await self.bot.player_messages.update_now_playing(ctx.guild.id)
            else:
                embed = EmbedManager.now_playing(
                    title=track.title,
                    author=track.author,
                    uri=track.uri,
                    length=track.length,
                    thumbnail_url=getattr(track, "artwork_url", None),
                    requester=ctx.author.mention,
                    volume=settings.get("volume", 50),
                )
                await ctx.send(embed=embed)

    # ============================================================
    # Playback Commands
    # ============================================================

    @commands.command(name="play", aliases=["p"])
    async def play(self, ctx: commands.Context, *, query: str) -> None:
        """Search for a track or play from URL. With select menu if multiple results."""
        if not await self._check_guild_and_channel(ctx):
            return
        if not await self._require_authorized(ctx):
            return

        async with ctx.typing():
            try:
                voice_channel, player = await self._ensure_voice(ctx)
            except (NotInVoiceChannel, DifferentVoiceChannel) as e:
                embed = build_error_embed(description=e.user_message)
                await ctx.send(embed=embed)
                return

            if not player:
                embed = build_error_embed(description="Failed to connect to voice channel.")
                await ctx.send(embed=embed)
                return

            # Search for tracks
            try:
                tracks = await wavelink.Playable.search(query)
            except Exception as e:
                logger.error("Search failed for '%s': %s", query, e)
                embed = build_error_embed(description="Failed to search for tracks. Is Lavalink running?")
                await ctx.send(embed=embed)
                return

            if not tracks:
                embed = TrackNotFound(query).user_message
                await ctx.send(embed=build_error_embed(description=embed))
                return

            # Handle playlist results (YouTube/Spotify playlist URL)
            if isinstance(tracks, wavelink.Playlist):
                await ctx.send(
                    embed=discord.Embed(
                        title="📀 Playlist Loaded",
                        description=f"Loaded **{len(tracks)}** tracks from playlist: **{tracks.name}**",
                        color=discord.Color.green(),
                    ),
                )
                for playlist_track in tracks:
                    await self._play_track(ctx, player, playlist_track)
                return

            # If query is URL or single exact match, play directly
            if _is_url(query) or len(tracks) == 1:
                track = tracks[0]
                await self._play_track(ctx, player, track)
                return

            # Otherwise show search select menu with top 5
            top_tracks = list(tracks)[:5]
            embed = EmbedManager.search_results_embed(query, top_tracks)
            view = SearchView(top_tracks, requester_id=ctx.author.id, bot=self.bot, guild_id=ctx.guild.id, query=query)
            await ctx.send(embed=embed, view=view)

    async def _run_controller(self, ctx: commands.Context, coro) -> None:
        result = await coro
        color = discord.Color.green() if result.ok else discord.Color.red()
        await ctx.send(embed=discord.Embed(description=result.message, color=color), delete_after=8 if result.ok else 12)
        if result.refresh_player and hasattr(self.bot, "player_messages"):
            await self.bot.player_messages.update_now_playing(ctx.guild.id)

    @commands.command(name="pause")
    async def pause(self, ctx: commands.Context) -> None:
        if not await self._check_guild_and_channel(ctx):
            return
        if not await self._require_authorized(ctx):
            return
        await self._run_controller(ctx, self.bot.player_controller.pause(ctx.guild.id, ctx.author))

    @commands.command(name="resume")
    async def resume(self, ctx: commands.Context) -> None:
        if not await self._check_guild_and_channel(ctx):
            return
        if not await self._require_authorized(ctx):
            return
        await self._run_controller(ctx, self.bot.player_controller.resume(ctx.guild.id, ctx.author))

    @commands.command(name="skip", aliases=["s", "next"])
    async def skip(self, ctx: commands.Context) -> None:
        if not await self._check_guild_and_channel(ctx):
            return
        if not await self._require_authorized(ctx):
            return
        await self._run_controller(ctx, self.bot.player_controller.skip(ctx.guild.id, ctx.author))

    @commands.command(name="stop")
    async def stop(self, ctx: commands.Context) -> None:
        if not await self._check_guild_and_channel(ctx):
            return
        if not await self._require_authorized(ctx):
            return
        await self._run_controller(ctx, self.bot.player_controller.stop(ctx.guild.id, ctx.author))
        if hasattr(self.bot, "player_messages"):
            await self.bot.player_messages.set_idle(ctx.guild.id)

    @commands.command(name="disconnect", aliases=["dc", "leave"])
    async def disconnect(self, ctx: commands.Context) -> None:
        if not await self._check_guild_and_channel(ctx):
            return
        if not await self._require_authorized(ctx):
            return
        await self._run_controller(ctx, self.bot.player_controller.disconnect(ctx.guild.id, ctx.author))

    # ============================================================
    # Queue Commands — now with pagination buttons
    # ============================================================

    @commands.command(name="queue", aliases=["q"])
    async def queue(self, ctx: commands.Context, page: int = 1) -> None:
        """Display the current music queue with pagination buttons."""
        if not await self._check_guild_and_channel(ctx):
            return
        if not await self._require_authorized(ctx):
            return

        player = _get_player(ctx)
        current_track = None
        if player and player.playing and player.last_track:
            current_track = {
                "title": player.last_track.title,
                "author": player.last_track.author,
                "uri": player.last_track.uri,
                "length": player.last_track.length,
                "requester_id": getattr(player.last_track, "requester_id", ctx.author.id),
            }

        queue_list = self.bot.queue_manager.get_all(ctx.guild.id)

        if not queue_list and not current_track:
            embed = build_error_embed(description="The queue is empty.")
            await ctx.send(embed=embed)
            return

        # Build embed
        embed = EmbedManager.queue_embed(
            queue=queue_list,
            current_track=current_track,
            page=page,
            guild_name=ctx.guild.name if ctx.guild else "Server",
        )
        # Paginated view with buttons
        view = QueuePaginatorView(
            bot=self.bot,
            guild_id=ctx.guild.id,
            requester_id=ctx.author.id,
            guild_name=ctx.guild.name if ctx.guild else "Server",
            page=page,
        )
        await ctx.send(embed=embed, view=view)

    @commands.command(name="nowplaying", aliases=["np", "current"])
    async def nowplaying(self, ctx: commands.Context) -> None:
        if not await self._check_guild_and_channel(ctx):
            return
        if not await self._require_authorized(ctx):
            return

        if hasattr(self.bot, "player_messages"):
            msg = await self.bot.player_messages.ensure_message(ctx.guild.id, channel=ctx.channel)
            await self.bot.player_messages.update_now_playing(ctx.guild.id)
            if msg:
                await ctx.send(
                    f"{EMOJI['music']} Player updated — use the buttons on the Now Playing message.",
                    delete_after=6,
                )
            else:
                await ctx.send(embed=build_error_embed(description="Could not create player message."))
            return

        player = _get_player(ctx)
        if not player or not player.playing or not player.last_track:
            embed = build_error_embed(description="Nothing is currently playing.")
            await ctx.send(embed=embed)
            return

        track = player.last_track
        embed = EmbedManager.now_playing(
            title=track.title,
            author=track.author,
            uri=track.uri,
            length=track.length,
            position=player.position if hasattr(player, "position") else 0,
            thumbnail_url=getattr(track, "artwork_url", None),
            volume=player.get_volume(),
        )
        await ctx.send(embed=embed)

    @commands.command(name="shuffle")
    async def shuffle(self, ctx: commands.Context) -> None:
        if not await self._check_guild_and_channel(ctx):
            return
        if not await self._require_authorized(ctx):
            return
        await self._run_controller(ctx, self.bot.player_controller.shuffle(ctx.guild.id, ctx.author))

    @commands.command(name="loop")
    async def loop(self, ctx: commands.Context, mode: str = "none") -> None:
        if not await self._check_guild_and_channel(ctx):
            return
        if not await self._require_authorized(ctx):
            return
        mode_lower = mode.strip().lower()
        if mode_lower not in ("none", "track", "queue"):
            embed = build_error_embed(description="Invalid mode. Use: none, track, or queue.")
            await ctx.send(embed=embed)
            return
        try:
            _, player = _voice_check(ctx)
        except (NotInVoiceChannel, DifferentVoiceChannel) as e:
            embed = build_error_embed(description=e.user_message)
            await ctx.send(embed=embed)
            return
        if not player:
            embed = build_error_embed(description="No active music session.")
            await ctx.send(embed=embed)
            return
        loop_mode = self.bot.queue_manager.set_loop(ctx.guild.id, mode_lower)
        mode_emojis = {
            LoopMode.NONE: EMOJI["loop_none"],
            LoopMode.TRACK: EMOJI["loop_track"],
            LoopMode.QUEUE: EMOJI["loop_queue"],
        }
        emoji = mode_emojis.get(loop_mode, EMOJI["loop_none"])
        embed = discord.Embed(
            title=f"{emoji} Loop Mode",
            description=f"Loop mode set to **{loop_mode.value}**.",
            color=discord.Color.blue(),
        )
        await ctx.send(embed=embed)
        if hasattr(self.bot, "player_messages"):
            await self.bot.player_messages.update_now_playing(ctx.guild.id)

    @commands.command(name="autoplay")
    async def autoplay(self, ctx: commands.Context, state: str = "toggle") -> None:
        if not await self._check_guild_and_channel(ctx):
            return
        if not await self._require_authorized(ctx):
            return
        try:
            _, player = _voice_check(ctx)
        except (NotInVoiceChannel, DifferentVoiceChannel) as e:
            embed = build_error_embed(description=e.user_message)
            await ctx.send(embed=embed)
            return
        if not player:
            embed = build_error_embed(description="No active music session.")
            await ctx.send(embed=embed)
            return
        state_lower = state.strip().lower()
        if state_lower == "on":
            enabled = True
        elif state_lower == "off":
            enabled = False
        else:
            enabled = None
        new_state = await player.toggle_autoplay(enabled)
        embed = discord.Embed(
            title="🤖 Autoplay",
            description=f"Autoplay has been **{'enabled' if new_state else 'disabled'}**.",
            color=discord.Color.green() if new_state else discord.Color.red(),
        )
        await ctx.send(embed=embed)

    # ============================================================
    # Settings Commands
    # ============================================================

    @commands.command(name="volume", aliases=["vol", "v"])
    async def volume(self, ctx: commands.Context, volume: int = 50) -> None:
        if not await self._check_guild_and_channel(ctx):
            return
        if not await self._require_authorized(ctx):
            return
        if volume < 0 or volume > 100:
            await ctx.send(embed=build_error_embed(description="Volume must be between 0 and 100."))
            return
        await self._run_controller(ctx, self.bot.player_controller.set_volume(ctx.guild.id, ctx.author, volume))

    @commands.command(name="ping")
    async def ping(self, ctx: commands.Context) -> None:
        if not await self._check_guild_and_channel(ctx):
            return
        if not await self._require_authorized(ctx):
            return
        bot_latency = round(self.bot.latency * 1000)
        lavalink_latency = "N/A"
        try:
            node = wavelink.Pool.get_node()
            if node:
                lavalink_latency = f"{round(node.latency)}ms"
        except Exception:
            pass
        embed = discord.Embed(title="🏓 Pong!", color=discord.Color.green())
        embed.add_field(name="Bot Latency", value=f"{bot_latency}ms", inline=True)
        embed.add_field(name="Lavalink Latency", value=lavalink_latency, inline=True)
        await ctx.send(embed=embed)

    @commands.command(name="help")
    async def help_command(self, ctx: commands.Context) -> None:
        if not await self._check_guild_and_channel(ctx):
            return
        embed = EmbedManager.help_embed()
        await ctx.send(embed=embed)

    # ============================================================
    # Favorites Commands — now with select menu + pagination
    # ============================================================

    @commands.command(name="favorite", aliases=["fav", "like"])
    async def favorite(self, ctx: commands.Context) -> None:
        if not await self._check_guild_and_channel(ctx):
            return
        if not await self._require_authorized(ctx):
            return
        await self._run_controller(ctx, self.bot.player_controller.favorite(ctx.guild.id, ctx.author))

    @commands.command(name="favorites")
    async def favorites(self, ctx: commands.Context, page: int = 1) -> None:
        """List your favorite tracks with pagination and play select."""
        if not await self._check_guild_and_channel(ctx):
            return
        if not await self._require_authorized(ctx):
            return

        favs, total = favorites_manager.get_favorites(
            user_id=str(ctx.author.id), page=page, db_path=self.bot.config.database_path
        )
        embed = EmbedManager.favorites_embed(favorites=favs, page=page, total=total)
        # If no favorites, just send embed
        if total == 0:
            await ctx.send(embed=embed)
            return

        view = FavoritesPaginatorView(
            bot=self.bot,
            guild_id=ctx.guild.id,
            user_id=ctx.author.id,
            initial_page=page,
            page_size=10,
        )
        await ctx.send(embed=embed, view=view)

    # ============================================================
    # Playlist Commands — enhanced with views
    # ============================================================

    @commands.command(name="playlist_create")
    async def playlist_create(self, ctx: commands.Context, name: str, *, description: str = "") -> None:
        if not await self._check_guild_and_channel(ctx):
            return
        if not await self._require_authorized(ctx):
            return
        playlist_id = playlist_manager.create_playlist(
            user_id=str(ctx.author.id),
            guild_id=str(ctx.guild.id),
            name=name,
            description=description,
            db_path=self.bot.config.database_path,
        )
        if playlist_id:
            embed = discord.Embed(
                title="📀 Playlist Created",
                description=f"**{name}** has been created.",
                color=discord.Color.green(),
            )
            embed.set_footer(text=f"ID: {playlist_id}")
        else:
            embed = build_error_embed(description=f"You already have a playlist named **{name}**.")
        await ctx.send(embed=embed)

    @commands.command(name="playlists")
    async def playlists(self, ctx: commands.Context) -> None:
        """List your playlists with interactive select."""
        if not await self._check_guild_and_channel(ctx):
            return
        if not await self._require_authorized(ctx):
            return

        playlists = playlist_manager.list_user_playlists(
            user_id=str(ctx.author.id), db_path=self.bot.config.database_path
        )

        if not playlists:
            embed = build_error_embed(description="You have no playlists. Create one with `!playlist_create <name>`.")
            await ctx.send(embed=embed)
            return

        embed = discord.Embed(
            title=f"{EMOJI['music']} Your Playlists",
            description=f"You have **{len(playlists)}** playlist(s). Select one to view tracks and play.",
            color=discord.Color.purple(),
        )
        lines = []
        for pl in playlists[:10]:
            lines.append(f"**{pl.get('name')}** — `{pl.get('track_count', 0)}` tracks — ID: `{pl.get('playlist_id')[:8]}...`")
        if lines:
            embed.add_field(name="Playlists", value="\n".join(lines), inline=False)
        embed.set_footer(text="Use the dropdown to browse • !playlist_show <id> for direct view")

        view = PlaylistListView(bot=self.bot, guild_id=ctx.guild.id, user_id=ctx.author.id, playlists=playlists)
        await ctx.send(embed=embed, view=view)

    @commands.command(name="playlist_show", aliases=["playlist_view", "pl_show"])
    async def playlist_show(self, ctx: commands.Context, playlist_id: str, page: int = 1) -> None:
        """Show a playlist with pagination and play buttons."""
        if not await self._check_guild_and_channel(ctx):
            return
        if not await self._require_authorized(ctx):
            return

        playlist = playlist_manager.get_playlist(playlist_id=playlist_id, db_path=self.bot.config.database_path)

        if not playlist:
            embed = build_error_embed(description="Playlist not found.")
            await ctx.send(embed=embed)
            return

        if not playlist.get("tracks"):
            embed = build_error_embed(description="This playlist has no tracks.")
            await ctx.send(embed=embed)
            return

        view = PlaylistDetailView(
            bot=self.bot, guild_id=ctx.guild.id, user_id=ctx.author.id, playlist=playlist, page=page, page_size=10
        )
        embed = view._build_embed()
        await ctx.send(embed=embed, view=view)

    @commands.command(name="playlist_add")
    async def playlist_add(self, ctx: commands.Context, playlist_id: str) -> None:
        if not await self._check_guild_and_channel(ctx):
            return
        if not await self._require_authorized(ctx):
            return
        player = _get_player(ctx)
        if not player or not player.playing or not player.last_track:
            embed = build_error_embed(description="Nothing is currently playing.")
            await ctx.send(embed=embed)
            return
        track = player.last_track
        success = playlist_manager.add_track(
            playlist_id=playlist_id,
            title=track.title,
            author=track.author,
            uri=track.uri,
            identifier=track.identifier,
            length=track.length,
            added_by=str(ctx.author.id),
            artwork_url=getattr(track, "artwork_url", None),
            db_path=self.bot.config.database_path,
        )
        if success:
            embed = discord.Embed(
                title="✅ Track Added",
                description=f"Added **{track.title}** to the playlist.",
                color=discord.Color.green(),
            )
        else:
            embed = build_error_embed(description="Could not add track. Check the playlist ID or track limit.")
        await ctx.send(embed=embed)

    @commands.command(name="playlist_remove")
    async def playlist_remove(self, ctx: commands.Context, playlist_id: str, position: int) -> None:
        if not await self._check_guild_and_channel(ctx):
            return
        if not await self._require_authorized(ctx):
            return
        success = playlist_manager.remove_track(
            playlist_id=playlist_id, position=position, user_id=str(ctx.author.id), db_path=self.bot.config.database_path
        )
        if success:
            embed = discord.Embed(
                title="✅ Track Removed",
                description=f"Removed track at position {position}.",
                color=discord.Color.green(),
            )
        else:
            embed = build_error_embed(description="Could not remove track. Check permissions or position.")
        await ctx.send(embed=embed)

    @commands.command(name="playlist_play")
    async def playlist_play(self, ctx: commands.Context, playlist_id: str) -> None:
        if not await self._check_guild_and_channel(ctx):
            return
        if not await self._require_authorized(ctx):
            return
        async with ctx.typing():
            playlist = playlist_manager.get_playlist(playlist_id=playlist_id, db_path=self.bot.config.database_path)
            if not playlist:
                embed = build_error_embed(description="Playlist not found.")
                await ctx.send(embed=embed)
                return
            if not playlist["tracks"]:
                embed = build_error_embed(description="This playlist has no tracks.")
                await ctx.send(embed=embed)
                return
            try:
                voice_channel, player = await self._ensure_voice(ctx)
            except (NotInVoiceChannel, DifferentVoiceChannel) as e:
                embed = build_error_embed(description=e.user_message)
                await ctx.send(embed=embed)
                return
            if not player:
                embed = build_error_embed(description="Failed to connect to voice.")
                await ctx.send(embed=embed)
                return
            for track_data in playlist["tracks"]:
                try:
                    tracks = await wavelink.Playable.search(track_data["uri"])
                    if tracks:
                        wavelink_track = tracks[0]
                        await self._play_track(ctx, player, wavelink_track)
                except Exception as e:
                    logger.debug("Failed to queue track %s: %s", track_data.get("title"), e)
            embed = discord.Embed(
                title="📀 Playing Playlist",
                description=f"Queued **{len(playlist['tracks'])}** tracks from **{playlist['name']}**.",
                color=discord.Color.purple(),
            )
            await ctx.send(embed=embed)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(MusicCommands(bot))
    logger.info("Music commands cog loaded with Phase 2 interactive views")
