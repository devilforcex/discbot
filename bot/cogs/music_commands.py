"""
Music command cog for the Discord Music Bot.
Implements all prefix commands for music playback, queue, favorites, and playlists.
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

logger = logging.getLogger(__name__)

# Commands that are allowed outside the music channel
ALLOWED_OUTSIDE_MUSIC_CHANNEL = {"help", "ping", "whoami", "requestaccess"}


def _voice_check(ctx: commands.Context) -> tuple:
    """Verify the user is in a voice channel and the bot can connect.

    Args:
        ctx: The command context.

    Returns:
        Tuple of (voice_channel, player).

    Raises:
        NotInVoiceChannel: If user is not in a voice channel.
        DifferentVoiceChannel: If user is in a different channel than bot.
    """
    # Check user voice state
    if not ctx.author.voice or not ctx.author.voice.channel:
        raise NotInVoiceChannel()

    voice_channel = ctx.author.voice.channel
    bot = ctx.bot

    # Check if bot is already connected
    existing_player = discord.utils.get(
        bot.voice_clients,
        guild__id=ctx.guild.id,
    )

    if existing_player:
        if existing_player.channel != voice_channel:
            raise DifferentVoiceChannel()
        return voice_channel, existing_player

    return voice_channel, None


def _get_player(ctx: commands.Context) -> Optional[Player]:
    """Get the player for the command's guild.

    Args:
        ctx: The command context.

    Returns:
        The Player instance, or None if not connected.
    """
    return discord.utils.get(
        ctx.bot.voice_clients,
        guild__id=ctx.guild.id,
    )


class MusicCommands(commands.Cog):
    """All prefix commands for music playback management."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # ============================================================
    # Authorization & Gatekeeping Helpers
    # ============================================================

    async def _check_guild_and_channel(self, ctx: commands.Context) -> bool:
        """Check guild restriction and music channel restriction.

        - Commands from non-target guilds are silently ignored.
        - Music commands outside the music channel get a rejection message.
        - Commands in ALLOWED_OUTSIDE_MUSIC_CHANNEL pass channel check.

        Returns:
            False if the command should be stopped, True if allowed.
        """
        config = self.bot.config

        # Guild restriction — silently ignore commands from other guilds
        if ctx.guild.id != config.guild_id:
            return False

        # Check if this command is allowed outside the music channel
        command_name = ctx.command.name if ctx.command else ""
        if command_name in ALLOWED_OUTSIDE_MUSIC_CHANNEL:
            return True

        # Channel restriction — reject with message if wrong channel
        if ctx.channel.id != config.music_channel_id:
            await ctx.send("❌ Music commands may only be used in the designated music channel.")
            return False

        return True

    async def _is_authorized(self, ctx: commands.Context) -> bool:
        """Check authorization in order: owner > blacklist > whitelist > deny.

        Returns:
            True if the user is authorized, False if not.
        """
        # 1. Owner always passes
        if ctx.author.id == self.bot.config.owner_id:
            return True

        user_id = str(ctx.author.id)

        try:
            conn = get_connection(self.bot.config.database_path)
            cursor = conn.cursor()

            # 2. Check blacklist
            cursor.execute(
                "SELECT 1 FROM blacklisted_users WHERE user_id = ?",
                (user_id,),
            )
            if cursor.fetchone():
                await ctx.send("❌ You are blacklisted.")
                return False

            # 3. Check whitelist (approved_users)
            cursor.execute(
                "SELECT 1 FROM approved_users WHERE user_id = ?",
                (user_id,),
            )
            if cursor.fetchone():
                return True

        except Exception as e:
            logger.error("Authorization check failed for user %s: %s", user_id, e)

        # 4. Deny
        await ctx.send("❌ You are not authorized to use this bot.")
        return False

    async def _require_authorized(self, ctx: commands.Context) -> bool:
        """Wrapper for command gating."""
        return await self._is_authorized(ctx)

    # ============================================================
    # Voice & Playback Helpers
    # ============================================================

    async def _ensure_voice(self, ctx: commands.Context) -> tuple:
        """Ensure user is in voice and bot can play.

        Args:
            ctx: The command context.

        Returns:
            Tuple of (voice_channel, player).
        """
        voice_channel, player = _voice_check(ctx)

        if player is None:
            player = await self.bot.lavalink.get_player(
                ctx.guild.id,
                voice_channel,
            )

        return voice_channel, player

    async def _play_track(
        self,
        ctx: commands.Context,
        player: Player,
        track: wavelink.Playable,
    ) -> None:
        """Play a track or add it to the queue.

        Args:
            ctx: The command context.
            player: The guild's player.
            track: The track to play.
        """
        # Get guild settings for volume
        settings = guild_settings.get(
            str(ctx.guild.id),
            self.bot.config.database_path,
        )

        # Set volume from settings
        await player.set_volume(settings.get("volume", 50))

        if player.playing:
            # Add to queue
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
            # Keep persistent player in sync
            if hasattr(self.bot, "player_messages"):
                await self.bot.player_messages.update_now_playing(ctx.guild.id)
        else:
            # Play immediately
            await player.play(track)
            self.bot.queue_manager.add_history(ctx.guild.id, {
                "title": track.title,
                "author": track.author,
                "uri": track.uri,
                "identifier": track.identifier,
                "length": track.length,
                "requester_id": ctx.author.id,
            })

            # Persistent NP message with buttons (track_start also refreshes)
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
        """Search for a track or play from a URL.

        Usage: !play <song name or URL>
        """
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

            track = tracks[0]

            # Handle playlist results
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

            await self._play_track(ctx, player, track)

    async def _run_controller(self, ctx: commands.Context, coro) -> None:
        """Run a PlayerController action and reply + refresh player."""
        result = await coro
        color = discord.Color.green() if result.ok else discord.Color.red()
        await ctx.send(
            embed=discord.Embed(description=result.message, color=color),
            delete_after=8 if result.ok else 12,
        )
        if result.refresh_player and hasattr(self.bot, "player_messages"):
            await self.bot.player_messages.update_now_playing(ctx.guild.id)

    @commands.command(name="pause")
    async def pause(self, ctx: commands.Context) -> None:
        """Pause the current playback. Usage: !pause"""
        if not await self._check_guild_and_channel(ctx):
            return
        if not await self._require_authorized(ctx):
            return
        await self._run_controller(
            ctx, self.bot.player_controller.pause(ctx.guild.id, ctx.author)
        )

    @commands.command(name="resume")
    async def resume(self, ctx: commands.Context) -> None:
        """Resume the paused playback. Usage: !resume"""
        if not await self._check_guild_and_channel(ctx):
            return
        if not await self._require_authorized(ctx):
            return
        await self._run_controller(
            ctx, self.bot.player_controller.resume(ctx.guild.id, ctx.author)
        )

    @commands.command(name="skip", aliases=["s", "next"])
    async def skip(self, ctx: commands.Context) -> None:
        """Skip the current track. Usage: !skip"""
        if not await self._check_guild_and_channel(ctx):
            return
        if not await self._require_authorized(ctx):
            return
        await self._run_controller(
            ctx, self.bot.player_controller.skip(ctx.guild.id, ctx.author)
        )

    @commands.command(name="stop")
    async def stop(self, ctx: commands.Context) -> None:
        """Stop playback and clear the queue. Usage: !stop"""
        if not await self._check_guild_and_channel(ctx):
            return
        if not await self._require_authorized(ctx):
            return
        await self._run_controller(
            ctx, self.bot.player_controller.stop(ctx.guild.id, ctx.author)
        )
        if hasattr(self.bot, "player_messages"):
            await self.bot.player_messages.set_idle(ctx.guild.id)

    @commands.command(name="disconnect", aliases=["dc", "leave"])
    async def disconnect(self, ctx: commands.Context) -> None:
        """Disconnect the bot from voice channel. Usage: !disconnect"""
        if not await self._check_guild_and_channel(ctx):
            return
        if not await self._require_authorized(ctx):
            return
        await self._run_controller(
            ctx, self.bot.player_controller.disconnect(ctx.guild.id, ctx.author)
        )

    # ============================================================
    # Queue Commands
    # ============================================================

    @commands.command(name="queue", aliases=["q"])
    async def queue(self, ctx: commands.Context, page: int = 1) -> None:
        """Display the current music queue.

        Usage: !queue [page]
        """
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

        embed = EmbedManager.queue_embed(
            queue=queue_list,
            current_track=current_track,
            page=page,
            guild_name=ctx.guild.name if ctx.guild else "Server",
        )
        await ctx.send(embed=embed)

    @commands.command(name="nowplaying", aliases=["np", "current"])
    async def nowplaying(self, ctx: commands.Context) -> None:
        """Show / refresh the persistent player with buttons.

        Usage: !nowplaying
        """
        if not await self._check_guild_and_channel(ctx):
            return
        if not await self._require_authorized(ctx):
            return

        if hasattr(self.bot, "player_messages"):
            msg = await self.bot.player_messages.ensure_message(
                ctx.guild.id, channel=ctx.channel
            )
            await self.bot.player_messages.update_now_playing(ctx.guild.id)
            if msg:
                await ctx.send(
                    f"{EMOJI['music']} Player updated — use the buttons on the Now Playing message.",
                    delete_after=6,
                )
            else:
                await ctx.send(
                    embed=build_error_embed(description="Could not create player message."),
                )
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
        """Shuffle the music queue. Usage: !shuffle"""
        if not await self._check_guild_and_channel(ctx):
            return
        if not await self._require_authorized(ctx):
            return
        await self._run_controller(
            ctx, self.bot.player_controller.shuffle(ctx.guild.id, ctx.author)
        )

    @commands.command(name="loop")
    async def loop(self, ctx: commands.Context, mode: str = "none") -> None:
        """Set the loop mode: none, track, queue.

        Usage: !loop <none|track|queue>
        """
        if not await self._check_guild_and_channel(ctx):
            return
        if not await self._require_authorized(ctx):
            return

        # Validate mode
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
        """Toggle autoplay for recommendations.

        Usage: !autoplay [on|off|toggle]
        """
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

        # Parse state
        state_lower = state.strip().lower()
        if state_lower == "on":
            enabled = True
        elif state_lower == "off":
            enabled = False
        else:
            enabled = None  # Toggle

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
        """Set the player volume (0-100). Usage: !volume <0-100>"""
        if not await self._check_guild_and_channel(ctx):
            return
        if not await self._require_authorized(ctx):
            return
        if volume < 0 or volume > 100:
            await ctx.send(embed=build_error_embed(description="Volume must be between 0 and 100."))
            return
        await self._run_controller(
            ctx,
            self.bot.player_controller.set_volume(ctx.guild.id, ctx.author, volume),
        )

    @commands.command(name="ping")
    async def ping(self, ctx: commands.Context) -> None:
        """Check bot and Lavalink latency.

        Usage: !ping
        """
        if not await self._check_guild_and_channel(ctx):
            return
        if not await self._require_authorized(ctx):
            return

        bot_latency = round(self.bot.latency * 1000)  # Convert to ms

        # Get Lavalink latency
        lavalink_latency = "N/A"
        try:
            node = wavelink.Pool.get_node()
            if node:
                lavalink_latency = f"{round(node.latency)}ms"
        except Exception:
            pass

        embed = discord.Embed(
            title="🏓 Pong!",
            color=discord.Color.green(),
        )
        embed.add_field(name="Bot Latency", value=f"{bot_latency}ms", inline=True)
        embed.add_field(name="Lavalink Latency", value=lavalink_latency, inline=True)
        await ctx.send(embed=embed)

    @commands.command(name="help")
    async def help_command(self, ctx: commands.Context) -> None:
        """Show available commands.

        Usage: !help
        """
        if not await self._check_guild_and_channel(ctx):
            return

        embed = EmbedManager.help_embed()
        await ctx.send(embed=embed)

    # ============================================================
    # Favorites Commands
    # ============================================================

    @commands.command(name="favorite", aliases=["fav", "like"])
    async def favorite(self, ctx: commands.Context) -> None:
        """Save the currently playing track to favorites. Usage: !favorite"""
        if not await self._check_guild_and_channel(ctx):
            return
        if not await self._require_authorized(ctx):
            return
        await self._run_controller(
            ctx, self.bot.player_controller.favorite(ctx.guild.id, ctx.author)
        )

    @commands.command(name="favorites")
    async def favorites(self, ctx: commands.Context, page: int = 1) -> None:
        """List your favorite tracks.

        Usage: !favorites [page]
        """
        if not await self._check_guild_and_channel(ctx):
            return
        if not await self._require_authorized(ctx):
            return

        favs, total = favorites_manager.get_favorites(
            user_id=str(ctx.author.id),
            page=page,
            db_path=self.bot.config.database_path,
        )

        embed = EmbedManager.favorites_embed(
            favorites=favs,
            page=page,
            total=total,
        )
        await ctx.send(embed=embed)

    # ============================================================
    # Playlist Commands
    # ============================================================

    @commands.command(name="playlist_create")
    async def playlist_create(self, ctx: commands.Context, name: str, *, description: str = "") -> None:
        """Create a new playlist.

        Usage: !playlist_create <name> [description]
        """
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
            embed = build_error_embed(
                description=f"You already have a playlist named **{name}**.",
            )

        await ctx.send(embed=embed)

    @commands.command(name="playlist_add")
    async def playlist_add(self, ctx: commands.Context, playlist_id: str) -> None:
        """Add the current track to a playlist.

        Usage: !playlist_add <playlist_id>
        """
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
            embed = build_error_embed(
                description="Could not add track. Check the playlist ID or track limit.",
            )

        await ctx.send(embed=embed)

    @commands.command(name="playlist_remove")
    async def playlist_remove(self, ctx: commands.Context, playlist_id: str, position: int) -> None:
        """Remove a track from a playlist.

        Usage: !playlist_remove <playlist_id> <position>
        """
        if not await self._check_guild_and_channel(ctx):
            return
        if not await self._require_authorized(ctx):
            return

        success = playlist_manager.remove_track(
            playlist_id=playlist_id,
            position=position,
            user_id=str(ctx.author.id),
            db_path=self.bot.config.database_path,
        )

        if success:
            embed = discord.Embed(
                title="✅ Track Removed",
                description=f"Removed track at position {position}.",
                color=discord.Color.green(),
            )
        else:
            embed = build_error_embed(
                description="Could not remove track. Check permissions or position.",
            )

        await ctx.send(embed=embed)

    @commands.command(name="playlist_play")
    async def playlist_play(self, ctx: commands.Context, playlist_id: str) -> None:
        """Play all tracks from a playlist.

        Usage: !playlist_play <playlist_id>
        """
        if not await self._check_guild_and_channel(ctx):
            return
        if not await self._require_authorized(ctx):
            return

        async with ctx.typing():
            # Get playlist
            playlist = playlist_manager.get_playlist(
                playlist_id=playlist_id,
                db_path=self.bot.config.database_path,
            )

            if not playlist:
                embed = build_error_embed(description="Playlist not found.")
                await ctx.send(embed=embed)
                return

            if not playlist["tracks"]:
                embed = build_error_embed(description="This playlist has no tracks.")
                await ctx.send(embed=embed)
                return

            # Ensure voice connection
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

            # Queue all tracks from playlist
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
    """Add the music commands cog to the bot."""
    await bot.add_cog(MusicCommands(bot))
    logger.info("Music commands cog loaded (prefix commands)")