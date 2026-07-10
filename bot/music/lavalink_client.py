"""
Lavalink client setup for the Discord Music Bot.
Manages Wavelink node connections, lifecycle, and event dispatching.
"""

import logging
from typing import Optional

import discord
import wavelink
from discord.ext import commands

from bot.config import Config
from bot.music.player import Player
from bot.music.queue_manager import QueueManager

logger = logging.getLogger(__name__)


class LavalinkClient:
    """Manages Lavalink node connection and lifecycle.

    Handles node registration, reconnection, and dispatches
    track events to the appropriate guild's player.
    """

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self._ready: bool = False

    @property
    def is_ready(self) -> bool:
        """Check if Lavalink node is connected and ready."""
        return self._ready

    async def setup(self, config: Config) -> None:
        """Initialize and connect to the Lavalink node.

        Args:
            config: Bot configuration with Lavalink settings.
        """
        # Register custom player
        wavelink.Player = Player

        node: wavelink.Node = wavelink.Node(
            uri=f"{'ws' if not config.lavalink_secure else 'wss'}://{config.lavalink_host}:{config.lavalink_port}",
            password=config.lavalink_password,
        )

        # Connect to Lavalink
        try:
            await wavelink.Pool.connect(
                client=self.bot,
                nodes=[node],
            )
            logger.info(
                "Connected to Lavalink at %s:%s",
                config.lavalink_host,
                config.lavalink_port,
            )
        except Exception as e:
            logger.error("Failed to connect to Lavalink: %s", e)
            raise

    async def get_player(
        self,
        guild_id: int,
        channel: Optional[discord.VoiceChannel] = None,
    ) -> Optional[Player]:
        """Get or create a player for a guild.

        Args:
            guild_id: Discord guild ID.
            channel: Optional voice channel to connect to.

        Returns:
            The Player instance, or None if not available.
        """
        player: Optional[Player] = self.bot.voice_clients and discord.utils.get(
            self.bot.voice_clients, guild__id=guild_id
        )

        if player is None and channel is not None:
            try:
                player = await channel.connect(cls=Player)
                logger.info("Connected to voice channel %s in guild %s", channel.name, guild_id)
            except Exception as e:
                logger.error("Failed to connect to voice channel: %s", e)
                return None

        return player

    async def destroy_player(self, guild_id: int) -> None:
        """Disconnect and clean up a player for a guild.

        Args:
            guild_id: Discord guild ID.
        """
        player: Optional[Player] = self.bot.voice_clients and discord.utils.get(
            self.bot.voice_clients, guild__id=guild_id
        )

        if player:
            await player.disconnect()
            logger.info("Disconnected player for guild %s", guild_id)


class WavelinkEvents(commands.Cog):
    """Event handler for Wavelink node and player events."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_wavelink_node_ready(self, payload: wavelink.NodeReadyEventPayload) -> None:
        """Handle Lavalink node ready event.

        Args:
            payload: Node ready event payload.
        """
        logger.info(
            "Wavelink node ready: %s | Resumed: %s",
            payload.node.uri,
            payload.resumed,
        )

    @commands.Cog.listener()
    async def on_wavelink_node_disconnected(self, payload: wavelink.NodeDisconnectedEventPayload) -> None:
        """Handle Lavalink node disconnection.

        Args:
            payload: Node disconnected event payload.
        """
        logger.warning(
            "Wavelink node disconnected: %s | Code: %s",
            payload.node.uri,
            payload.code,
        )

    @commands.Cog.listener()
    async def on_wavelink_track_start(self, payload: wavelink.TrackStartEventPayload) -> None:
        """Handle track start event.

        Args:
            payload: Track start event payload.
        """
        player: Player = payload.player
        track = payload.track

        if player and track:
            player.store_track(track)
            guild_id = player.guild.id
            logger.info("Started playing: %s in guild %s", track.title, guild_id)

            # Refresh persistent Now Playing message + buttons
            mgr = getattr(self.bot, "player_messages", None)
            if mgr:
                try:
                    await mgr.update_now_playing(guild_id)
                except Exception as e:
                    logger.debug("Player message update on track_start failed: %s", e)

    @commands.Cog.listener()
    async def on_wavelink_track_end(self, payload: wavelink.TrackEndEventPayload) -> None:
        """Handle track end event.

        Args:
            payload: Track end event payload.
        """
        player: Player = payload.player
        track = payload.track

        if not player or not track:
            return

        guild_id = player.guild.id
        logger.info("Track ended: %s in guild %s | Reason: %s", track.title, guild_id, payload.reason)

        # Save to database history
        self._save_playback_history(guild_id, track, player)

        # Handle loop track — replay same track
        loop_mode = self.bot.queue_manager.get_loop(guild_id)
        from bot.music.queue_manager import LoopMode

        if loop_mode == LoopMode.TRACK and payload.reason != "replaced":
            try:
                await player.play(track)
                return
            except Exception as e:
                logger.error("Loop track replay failed: %s", e)

        # Handle autoplay / next
        if player.autoplay_enabled and payload.reason != "replaced":
            await self._handle_autoplay(player, guild_id)
        elif payload.reason != "replaced":
            await self._play_next(player)

        # If nothing left playing, set idle player message
        if not player.playing:
            mgr = getattr(self.bot, "player_messages", None)
            if mgr:
                try:
                    await mgr.set_idle(guild_id)
                except Exception as e:
                    logger.debug("Player idle update failed: %s", e)

    @commands.Cog.listener()
    async def on_wavelink_track_stuck(self, payload: wavelink.TrackStuckEventPayload) -> None:
        """Handle track stuck event.

        Args:
            payload: Track stuck event payload.
        """
        player = payload.player
        logger.warning(
            "Track stuck in guild %s: %s | Threshold: %dms",
            player.guild.id if player else "unknown",
            payload.track.title if payload.track else "unknown",
            payload.threshold_ms,
        )

        # Skip to next track
        await self._play_next(player)

    @commands.Cog.listener()
    async def on_wavelink_track_exception(self, payload: wavelink.TrackExceptionEventPayload) -> None:
        """Handle track exception event.

        Args:
            payload: Track exception event payload.
        """
        player = payload.player
        logger.error(
            "Track exception in guild %s: %s | Error: %s",
            player.guild.id if player else "unknown",
            payload.track.title if payload.track else "unknown",
            payload.exception,
        )

        # Skip to next track
        await self._play_next(player)

    async def _handle_autoplay(self, player: Player, guild_id: int) -> None:
        """Handle autoplay logic when a track ends.

        Args:
            player: The guild's player.
            guild_id: Discord guild ID.
        """
        if not self.bot.queue_manager.is_empty(guild_id):
            # Queue has tracks, just play next
            await self._play_next(player)
        else:
            # Queue is empty, try to get an autoplay recommendation
            autoplay_track = await player.get_autoplay_track()
            if autoplay_track:
                self.bot.queue_manager.add_front(guild_id, {
                    "title": autoplay_track.title,
                    "author": autoplay_track.author,
                    "uri": autoplay_track.uri,
                    "identifier": autoplay_track.identifier,
                    "length": autoplay_track.length,
                    "artwork_url": getattr(autoplay_track, "artwork_url", None),
                })
                await self._play_next(player)

    async def _play_next(self, player: Player) -> None:
        """Play the next track in the queue.

        Args:
            player: The guild's player.
        """
        guild_id = player.guild.id
        next_track_data = self.bot.queue_manager.get_next(guild_id)

        if next_track_data is None:
            logger.info("Queue empty for guild %s, playback stopped", guild_id)
            mgr = getattr(self.bot, "player_messages", None)
            if mgr:
                try:
                    await mgr.set_idle(guild_id)
                except Exception:
                    pass
            return

        # Search for the track by URL or identifier
        try:
            tracks = await wavelink.Playable.search(next_track_data["uri"])
            if tracks:
                track = tracks[0]
                await player.play(track)
                logger.info("Playing next track: %s in guild %s", track.title, guild_id)
        except Exception as e:
            logger.error("Failed to play next track in guild %s: %s", guild_id, e)

    def _save_playback_history(self, guild_id: int, track: wavelink.Playable, player: Player) -> None:
        """Save track playback to database.

        Args:
            guild_id: Discord guild ID.
            track: The track that finished playing.
            player: The guild's player.
        """
        try:
            from bot.database import history_manager

            # Get the requester from the last track data in queue manager
            history = self.bot.queue_manager.get_history(guild_id, limit=1)
            requester_id = history[0].get("requester_id", 0) if history else 0

            history_manager.add(
                guild_id=str(guild_id),
                user_id=str(requester_id),
                title=track.title,
                author=track.author,
                uri=track.uri,
                identifier=track.identifier,
                length=track.length,
                db_path=self.bot.config.database_path,
            )
        except Exception as e:
            logger.debug("Failed to save playback history: %s", e)


async def setup(bot: commands.Bot) -> None:
    """Add the Wavelink events cog to the bot."""
    await bot.add_cog(WavelinkEvents(bot))
    logger.info("Wavelink events cog loaded")