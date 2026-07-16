"""Player state builder and embed rendering."""

from __future__ import annotations

import discord

from bot.music.embed_manager import EmbedManager
from bot.music.player_view import PlayerView


class PlayerStateBuilder:
    def __init__(self, bot):
        self.bot = bot

    def get_channel(self, guild_id: int) -> discord.TextChannel | None:
        guild = self.bot.get_guild(guild_id)
        if not guild:
            return None
        ch = guild.get_channel(self.bot.config.music_channel_id)
        if isinstance(ch, discord.TextChannel):
            return ch
        if isinstance(guild.system_channel, discord.TextChannel):
            return guild.system_channel
        for c in guild.text_channels:
            if c.permissions_for(guild.me).send_messages:
                return c
        return None

    def build_view(self, guild_id: int) -> PlayerView:
        return PlayerView(bot=self.bot, guild_id=guild_id)

    def player_state(self, guild_id: int) -> dict:
        player = discord.utils.get(self.bot.voice_clients, guild__id=guild_id)
        loop = self.bot.queue_manager.get_loop(guild_id)
        queue_len = self.bot.queue_manager.get_length(guild_id)

        is_active = bool(
            player and (getattr(player, "playing", False) or getattr(player, "paused", False))
        )
        if not player or not getattr(player, "last_track", None) or not is_active:
            return {
                "playing": False,
                "paused": False,
                "volume": 50,
                "loop": loop,
                "queue_len": queue_len,
                "autoplay": getattr(player, "autoplay_enabled", False) if player else False,
                "active_filter": getattr(player, "active_filter", "off") if player else "off",
            }

        track = player.last_track
        return {
            "playing": True,
            "paused": player.paused,
            "title": track.title,
            "author": track.author,
            "uri": track.uri,
            "length": track.length,
            "position": player.position if hasattr(player, "position") else 0,
            "thumbnail": getattr(track, "artwork_url", None),
            "volume": player.get_volume() if hasattr(player, "get_volume") else 50,
            "loop": loop,
            "queue_len": queue_len,
            "autoplay": getattr(player, "autoplay_enabled", False),
            "active_filter": getattr(player, "active_filter", "off"),
            "requester": None,
        }

    def build_embed(self, guild_id: int) -> discord.Embed:
        state = self.player_state(guild_id)
        if not state["playing"]:
            return EmbedManager.player_idle_embed(queue_len=state["queue_len"], loop=state["loop"])
        return EmbedManager.player_now_playing_embed(
            title=state["title"],
            author=state["author"],
            uri=state["uri"],
            length=state["length"],
            position=state["position"],
            thumbnail_url=state.get("thumbnail"),
            volume=state["volume"],
            paused=state["paused"],
            loop=state["loop"],
            autoplay=state["autoplay"],
            queue_len=state["queue_len"],
            requester=state.get("requester"),
            active_filter=state.get("active_filter", "off"),
        )
