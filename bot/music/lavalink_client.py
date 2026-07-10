"""
Lavalink client setup for the Discord Music Bot.
Manages Wavelink node connections, lifecycle, and event dispatching.
"""

import inspect
import logging
from typing import Optional

import discord
import wavelink
from discord.ext import commands

from bot.config import Config
from bot.music.player import Player

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

        # Avoid duplicate connection attempts when setup() is called from
        # reconnect logic while the pool is already healthy. If a stale
        # disconnected node is still registered, close the pool before creating
        # a replacement node.
        existing = None
        try:
            existing = wavelink.Pool.get_node()
            if existing and getattr(existing, "is_connected", False):
                self._ready = True
                logger.debug("Lavalink node already connected: %s", existing.uri)
                return
        except Exception:
            # No node registered yet (or Pool cannot resolve a node). Continue
            # with normal connection setup.
            existing = None

        if existing:
            close = getattr(wavelink.Pool, "close", None)
            if close is not None:
                result = close()
                if inspect.isawaitable(result):
                    await result

        # Wavelink v3 expects the Lavalink REST URI (http/https). It opens the
        # websocket session internally; passing ws:// here breaks node setup on
        # current Wavelink releases.
        scheme = "https" if config.lavalink_secure else "http"
        uri = f"{scheme}://{config.lavalink_host}:{config.lavalink_port}"
        node: wavelink.Node = wavelink.Node(
            uri=uri,
            password=config.lavalink_password,
        )

        # Connect to Lavalink
        try:
            await wavelink.Pool.connect(
                client=self.bot,
                nodes=[node],
            )
            self._ready = True
            logger.info("Connected to Lavalink at %s", uri)
        except Exception as e:
            self._ready = False
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
        player: Optional[Player] = (
            discord.utils.get(self.bot.voice_clients, guild__id=guild_id)
            if self.bot.voice_clients
            else None
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
        player: Optional[Player] = (
            discord.utils.get(self.bot.voice_clients, guild__id=guild_id)
            if self.bot.voice_clients
            else None
        )

        if player:
            await player.disconnect()
            logger.info("Disconnected player for guild %s", guild_id)

    async def close(self) -> None:
        """Disconnect voice clients and close all Wavelink nodes if supported."""
        self._ready = False

        for voice_client in list(getattr(self.bot, "voice_clients", [])):
            try:
                await voice_client.disconnect(force=True)
            except TypeError:
                await voice_client.disconnect()
            except Exception as e:
                logger.debug("Voice client disconnect failed during shutdown: %s", e)

        close = getattr(wavelink.Pool, "close", None)
        if close is None:
            return

        result = close()
        if inspect.isawaitable(result):
            await result


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
        if hasattr(self.bot, "lavalink"):
            self.bot.lavalink._ready = True
        if getattr(self.bot, "_lavalink_reconnect_task", None):
            task = self.bot._lavalink_reconnect_task
            if task and not task.done():
                task.cancel()
        if hasattr(self.bot, "_lavalink_reconnect_attempt"):
            self.bot._lavalink_reconnect_attempt = 0

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
        if hasattr(self.bot, "lavalink"):
            self.bot.lavalink._ready = False

        logger.warning(
            "Wavelink node disconnected: %s | Code: %s",
            payload.node.uri,
            payload.code,
        )

        scheduler = getattr(self.bot, "_schedule_lavalink_reconnect", None)
        if scheduler:
            scheduler()

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
        if player:
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
        if player:
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
        """Play the next playable track in the queue.

        Invalid or unavailable queued entries are skipped so one bad URL does
        not stall the entire queue.

        Args:
            player: The guild's player.
        """
        guild_id = player.guild.id
        max_attempts = max(1, self.bot.queue_manager.get_length(guild_id) + 1)

        for _ in range(max_attempts):
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

            uri = next_track_data.get("uri")
            if not uri:
                logger.warning("Skipping queued track without URI in guild %s: %s", guild_id, next_track_data)
                self._discard_queued_track(guild_id, next_track_data)
                continue

            # Search for the track by URL or identifier.
            try:
                tracks = await wavelink.Playable.search(uri)
            except Exception as e:
                logger.error("Failed to resolve queued track in guild %s: %s", guild_id, e)
                continue

            if not tracks:
                logger.warning("Queued track no longer found in guild %s: %s", guild_id, uri)
                self._discard_queued_track(guild_id, next_track_data)
                continue

            track = tracks[0]
            await player.play(track)
            self.bot.queue_manager.add_history(guild_id, next_track_data)
            logger.info("Playing next track: %s in guild %s", track.title, guild_id)
            return

        logger.warning("No playable queued tracks found for guild %s after %d attempt(s)", guild_id, max_attempts)
        mgr = getattr(self.bot, "player_messages", None)
        if mgr:
            try:
                await mgr.set_idle(guild_id)
            except Exception:
                pass

    def _discard_queued_track(self, guild_id: int, track_data: dict) -> None:
        """Remove a bad queued track if loop-queue reinserted it."""
        try:
            self.bot.queue_manager.remove_by_uri(guild_id, track_data)
        except Exception as e:
            logger.debug("Failed to discard bad queued track in guild %s: %s", guild_id, e)

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