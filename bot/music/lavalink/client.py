"""Lavalink client — connection management."""
from __future__ import annotations

import inspect
import logging
from typing import Optional

import discord
import wavelink

from bot.config import Config
from bot.music.player import Player

logger = logging.getLogger(__name__)


class LavalinkClient:
    def __init__(self, bot):
        self.bot = bot
        self._ready: bool = False

    @property
    def is_ready(self) -> bool:
        return self._ready

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

    async def get_player(self, guild_id: int, channel: Optional[discord.VoiceChannel] = None) -> Optional[Player]:
        player: Optional[Player] = (
            discord.utils.get(self.bot.voice_clients, guild__id=guild_id) if self.bot.voice_clients else None
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
        player: Optional[Player] = (
            discord.utils.get(self.bot.voice_clients, guild__id=guild_id) if self.bot.voice_clients else None
        )
        if player:
            await player.disconnect()
            logger.info("Disconnected player for guild %s", guild_id)

    async def close(self) -> None:
        self._ready = False
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
