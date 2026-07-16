"""Lavalink client — connection management."""

from __future__ import annotations

import asyncio
import inspect
import logging
import random

import discord
import wavelink

from bot.config import Config
from bot.music.player import Player

logger = logging.getLogger(__name__)


class LavalinkClient:
    def __init__(self, bot):
        self.bot = bot
        self._ready: bool = False
        self._reconnect_attempt: int = 0
        self._max_reconnect_attempts: int = 10
        self._base_reconnect_delay: float = 2.0  # seconds
        self._max_reconnect_delay: float = 300.0  # 5 minutes
        self._reconnect_task: asyncio.Task | None = None

    @property
    def is_ready(self) -> bool:
        return self._ready

    async def health_check(self) -> dict:
        """Check Lavalink node health."""
        try:
            node = wavelink.Pool.get_node()
            if not node:
                return {"healthy": False, "reason": "No node connected"}
            connected = node.status == wavelink.NodeStatus.CONNECTED
            if not connected:
                return {"healthy": False, "reason": f"Node not connected (status: {node.status})"}
            # Try to get stats from Lavalink
            stats = None
            if hasattr(node, "fetch_stats"):
                stats = await node.fetch_stats()
            return {
                "healthy": True,
                "connected": True,
                "uri": node.uri,
                "players": len(getattr(node, "players", {})),
                "stats": stats,
            }
        except Exception as e:
            logger.warning("Lavalink health check failed: %s", e)
            return {"healthy": False, "reason": str(e)}

    async def setup(self, config: Config) -> None:
        wavelink.Player = Player

        existing = None
        try:
            existing = wavelink.Pool.get_node()
            if existing and getattr(existing, "is_connected", False):
                self._ready = True
                logger.debug("Lavalink node already connected: %s", existing.uri)
                return
        except Exception:
            existing = None

        if existing:
            close = getattr(wavelink.Pool, "close", None)
            if close is not None:
                result = close()
                if inspect.isawaitable(result):
                    await result

        scheme = "https" if config.lavalink_secure else "http"
        uri = f"{scheme}://{config.lavalink_host}:{config.lavalink_port}"
        node: wavelink.Node = wavelink.Node(uri=uri, password=config.lavalink_password)

        try:
            await wavelink.Pool.connect(client=self.bot, nodes=[node])
            self._ready = True
            logger.info("Connected to Lavalink at %s", uri)
        except Exception as e:
            self._ready = False
            logger.error("Failed to connect to Lavalink: %s", e)
            raise

    async def get_player(
        self, guild_id: int, channel: discord.VoiceChannel | None = None
    ) -> Player | None:
        player: Player | None = (
            discord.utils.get(self.bot.voice_clients, guild__id=guild_id)  # type: ignore[return-value]
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
        player: Player | None = (
            discord.utils.get(self.bot.voice_clients, guild__id=guild_id)  # type: ignore[return-value]
            if self.bot.voice_clients
            else None
        )
        if player:
            await player.disconnect()
            logger.info("Disconnected player for guild %s", guild_id)

    async def close(self) -> None:
        self._ready = False
        # Cancel any pending reconnect
        if self._reconnect_task and not self._reconnect_task.done():
            self._reconnect_task.cancel()
        for voice_client in list(getattr(self.bot, "voice_clients", [])):
            try:
                await voice_client.disconnect(force=True)
            except TypeError:
                await voice_client.disconnect()
            except Exception as e:
                logger.debug("Voice disconnect failed during shutdown: %s", e)

        close = getattr(wavelink.Pool, "close", None)
        if close is None:
            return
        result = close()
        if inspect.isawaitable(result):
            await result

    def schedule_reconnect(self) -> None:
        """Schedule a Lavalink reconnect with exponential backoff."""
        if self._reconnect_task and not self._reconnect_task.done():
            return  # Already scheduled

        self._reconnect_task = asyncio.create_task(self._reconnect_with_backoff())

    async def _reconnect_with_backoff(self) -> None:
        """Reconnect to Lavalink with exponential backoff and jitter."""
        while self._reconnect_attempt < self._max_reconnect_attempts:
            self._reconnect_attempt += 1
            delay = min(
                self._base_reconnect_delay * (2 ** (self._reconnect_attempt - 1))
                + random.uniform(0, 1),
                self._max_reconnect_delay,
            )
            logger.info(
                "Scheduling Lavalink reconnect attempt %d/%d in %.1fs",
                self._reconnect_attempt,
                self._max_reconnect_attempts,
                delay,
            )
            await asyncio.sleep(delay)

            try:
                node = wavelink.Pool.get_node()
                if node and getattr(node, "is_connected", False):
                    self._ready = True
                    self._reconnect_attempt = 0
                    logger.info("Lavalink reconnected successfully")
                    return
                # Try to reconnect
                await self.setup(self.bot.config)
                self._ready = True
                self._reconnect_attempt = 0
                logger.info("Lavalink reconnected successfully")
                return
            except Exception as e:
                logger.warning(
                    "Lavalink reconnect attempt %d failed: %s", self._reconnect_attempt, e
                )

        logger.error("Max Lavalink reconnect attempts (%d) reached", self._max_reconnect_attempts)
