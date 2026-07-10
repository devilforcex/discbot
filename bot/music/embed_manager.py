"""
Facade for embeds — keeps old import path working while actual logic lives in
bot.music.embeds/* modules.
"""
from __future__ import annotations

from typing import Optional, Union

import discord

from bot.music.queue_manager import LoopMode
from .embeds.common import build_progress_bar as _build_bar
from .embeds.common import format_duration as _fmt
from .embeds import (
    player_idle_embed,
    player_now_playing_embed,
    queue_embed,
    playlist_embed,
    favorites_embed,
    search_results_embed,
    track_added,
    filter_embed,
    help_embed,
)


class EmbedManager:
    """Backwards-compatible static facade."""

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
        active_filter: str = "off",
    ) -> discord.Embed:
        return player_now_playing_embed(
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
            active_filter=active_filter,
        )

    @staticmethod
    def player_now_playing_embed(*args, **kwargs) -> discord.Embed:
        return player_now_playing_embed(*args, **kwargs)

    @staticmethod
    def player_idle_embed(*args, **kwargs) -> discord.Embed:
        return player_idle_embed(*args, **kwargs)

    @staticmethod
    def queue_embed(*args, **kwargs) -> discord.Embed:
        return queue_embed(*args, **kwargs)

    @staticmethod
    def playlist_embed(*args, **kwargs) -> discord.Embed:
        return playlist_embed(*args, **kwargs)

    @staticmethod
    def favorites_embed(*args, **kwargs) -> discord.Embed:
        return favorites_embed(*args, **kwargs)

    @staticmethod
    def help_embed() -> discord.Embed:
        return help_embed()

    @staticmethod
    def search_results_embed(query: str, tracks: list) -> discord.Embed:
        return search_results_embed(query, tracks)

    @staticmethod
    def filter_embed(active_filter: str = "off") -> discord.Embed:
        return filter_embed(active_filter)

    @staticmethod
    def track_added(*args, **kwargs) -> discord.Embed:
        return track_added(*args, **kwargs)

    # Legacy helpers — kept because many views used EmbedManager._format_duration
    @staticmethod
    def _format_duration(milliseconds: int) -> str:
        return _fmt(milliseconds)

    @staticmethod
    def _build_progress_bar(current: int, total: int, length: int = 18, bar_len: Optional[int] = None) -> str:
        return _build_bar(current, total, length, bar_len)
