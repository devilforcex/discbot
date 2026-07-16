"""Wavelink event handlers — split from monolithic lavalink_client.py."""

from __future__ import annotations

import contextlib
import logging

import discord
import wavelink
from discord.ext import commands

from bot.music.player import Player

logger = logging.getLogger(__name__)


def _get_now_playing_data(bot: commands.Bot, guild_id: int) -> dict:
    """Build the now-playing payload for WebSocket broadcast."""
    player = discord.utils.get(bot.voice_clients, guild__id=guild_id)
    if player and getattr(player, "playing", False) and getattr(player, "last_track", None):
        track = player.last_track
        loop_mode = None
        try:
            mode = bot.queue_manager.get_loop(guild_id)
            loop_mode = mode.value if hasattr(mode, "value") else str(mode)
        except Exception:
            pass
        return {
            "playing": True,
            "title": track.title,
            "author": track.author,
            "uri": track.uri,
            "length": track.length,
            "position": player.position if hasattr(player, "position") else 0,
            "paused": player.paused,
            "volume": player.get_volume() if hasattr(player, "get_volume") else 50,
            "artwork_url": getattr(track, "artwork_url", None),
            "autoplay": getattr(player, "autoplay_enabled", False),
            "loop": loop_mode,
            "queue_length": bot.queue_manager.get_length(guild_id),
        }
    return {"playing": False, "queue_length": bot.queue_manager.get_length(guild_id)}


def _get_queue_data(bot: commands.Bot, guild_id: int) -> dict:
    """Build the queue payload for WebSocket broadcast."""
    tracks = bot.queue_manager.get_all_as_dicts(guild_id)
    return {
        "guild_id": guild_id,
        "queue_length": len(tracks),
        "tracks": tracks,
    }


async def _broadcast_player_update(bot: commands.Bot, guild_id: int) -> None:
    """Broadcast now-playing + queue update to all connected WebSocket clients."""
    try:
        from bot.dashboard.ws_manager import ws_manager

        now_playing = _get_now_playing_data(bot, guild_id)
        queue = _get_queue_data(bot, guild_id)
        await ws_manager.broadcast(guild_id, "player_update", {
            "now_playing": now_playing,
            "queue": queue,
        })
    except Exception as e:
        logger.debug("WS broadcast failed for guild %s: %s", guild_id, e)


class WavelinkEvents(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self._autoplay_failures: dict[int, int] = {}
        self._max_autoplay_failures = 3

    @commands.Cog.listener()
    async def on_wavelink_node_ready(self, payload: wavelink.NodeReadyEventPayload) -> None:
        if hasattr(self.bot, "lavalink"):
            self.bot.lavalink._ready = True
        if getattr(self.bot, "_lavalink_reconnect_task", None):
            task = self.bot._lavalink_reconnect_task
            if task and not task.done():
                task.cancel()
        if hasattr(self.bot, "_lavalink_reconnect_attempt"):
            self.bot._lavalink_reconnect_attempt = 0
        logger.info("Wavelink node ready: %s | Resumed: %s", payload.node.uri, payload.resumed)

    @commands.Cog.listener()
    async def on_wavelink_node_disconnected(
        self, payload: wavelink.NodeDisconnectedEventPayload
    ) -> None:
        if hasattr(self.bot, "lavalink"):
            self.bot.lavalink._ready = False
            self.bot.lavalink.schedule_reconnect()
        logger.warning("Wavelink node disconnected: %s", payload.node.uri)

    @commands.Cog.listener()
    async def on_wavelink_track_start(self, payload: wavelink.TrackStartEventPayload) -> None:
        player: Player = payload.player
        track = payload.track
        if player and track:
            player.store_track(track)
            guild_id = player.guild.id
            logger.info("Started playing: %s in guild %s", track.title, guild_id)
            mgr = getattr(self.bot, "player_messages", None)
            if mgr:
                try:
                    await mgr.update_now_playing(guild_id)
                except Exception as e:
                    logger.debug("Player message update on track_start failed: %s", e)
            await _broadcast_player_update(self.bot, guild_id)

    @commands.Cog.listener()
    async def on_wavelink_track_end(self, payload: wavelink.TrackEndEventPayload) -> None:
        player: Player = payload.player
        track = payload.track
        if not player or not track:
            return
        guild_id = player.guild.id
        logger.info(
            "Track ended: %s in guild %s | Reason: %s", track.title, guild_id, payload.reason
        )
        self._save_playback_history(guild_id, track, player)
        loop_mode = self.bot.queue_manager.get_loop(guild_id)
        from bot.music.queue_manager import LoopMode

        if loop_mode == LoopMode.TRACK and payload.reason != "replaced":
            try:
                await player.play(track)
                return
            except Exception as e:
                logger.error("Loop track replay failed: %s", e)
        if player.autoplay_enabled and payload.reason != "replaced":
            await self._handle_autoplay(player, guild_id)
        elif payload.reason != "replaced":
            await self._play_next(player)
        if not player.playing:
            mgr = getattr(self.bot, "player_messages", None)
            if mgr:
                try:
                    await mgr.set_idle(guild_id)
                except Exception as e:
                    logger.debug("Player idle update failed: %s", e)
        await _broadcast_player_update(self.bot, guild_id)

    @commands.Cog.listener()
    async def on_wavelink_track_stuck(self, payload: wavelink.TrackStuckEventPayload) -> None:
        player = payload.player
        logger.warning(
            "Track stuck in guild %s: %s | Threshold: %dms",
            player.guild.id if player else "unknown",
            payload.track.title if payload.track else "unknown",
            payload.threshold_ms,
        )
        if player:
            await self._play_next(player)
            await _broadcast_player_update(self.bot, player.guild.id)

    @commands.Cog.listener()
    async def on_wavelink_track_exception(
        self, payload: wavelink.TrackExceptionEventPayload
    ) -> None:
        player = payload.player
        logger.error(
            "Track exception in guild %s: %s | Error: %s",
            player.guild.id if player else "unknown",
            payload.track.title if payload.track else "unknown",
            payload.exception,
        )
        if player:
            await self._play_next(player)
            await _broadcast_player_update(self.bot, player.guild.id)

    async def _handle_autoplay(self, player: Player, guild_id: int) -> None:
        # Circuit breaker: skip autoplay if too many failures
        if self._autoplay_failures.get(guild_id, 0) >= self._max_autoplay_failures:
            logger.warning("Autoplay circuit breaker open for guild %s", guild_id)
            return
        if not self.bot.queue_manager.is_empty(guild_id):
            await self._play_next(player)
        else:
            autoplay_track = await player.get_autoplay_track()
            if autoplay_track:
                self.bot.queue_manager.add_front(guild_id, autoplay_track)
                await self._play_next(player)
            else:
                # Track autoplay failure for circuit breaker
                self._autoplay_failures[guild_id] = self._autoplay_failures.get(guild_id, 0) + 1
                logger.debug(
                    "Autoplay failed for guild %s (count: %d)",
                    guild_id,
                    self._autoplay_failures.get(guild_id),
                )

    async def _play_next(self, player: Player) -> None:
        guild_id = player.guild.id
        max_attempts = max(1, self.bot.queue_manager.get_length(guild_id) + 1)
        for _ in range(max_attempts):
            next_track = self.bot.queue_manager.get_next(guild_id)
            if next_track is None:
                logger.info("Queue empty for guild %s, playback stopped", guild_id)
                mgr = getattr(self.bot, "player_messages", None)
                if mgr:
                    with contextlib.suppress(Exception):
                        await mgr.set_idle(guild_id)
                return
            try:
                await player.play(next_track)
                self.bot.queue_manager.add_history(guild_id, next_track)
                logger.info(
                    "Playing next track: %s in guild %s",
                    getattr(next_track, "title", "?"),
                    guild_id,
                )
                return
            except Exception as e:
                logger.error("Failed to play queued track in guild %s: %s", guild_id, e)
                continue
        logger.warning(
            "No playable queued tracks for guild %s after %d attempt(s)", guild_id, max_attempts
        )
        mgr = getattr(self.bot, "player_messages", None)
        if mgr:
            with contextlib.suppress(Exception):
                await mgr.set_idle(guild_id)

    def _save_playback_history(
        self, guild_id: int, track: wavelink.Playable, player: Player
    ) -> None:
        try:
            from bot.database import history_manager

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
    await bot.add_cog(WavelinkEvents(bot))
    logger.info("Wavelink events cog loaded")
