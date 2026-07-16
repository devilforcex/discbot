"""Playback cog — play, pause, resume, skip, stop, disconnect."""

from __future__ import annotations

import contextlib
import logging

import discord
import wavelink
from discord.ext import commands

from bot.core.errors import (
    DifferentVoiceChannel,
    NotInVoiceChannel,
    TrackNotFound,
    build_error_embed,
)
from bot.database import guild_settings
from bot.music.embed_manager import EmbedManager
from bot.music.player import Player
from bot.music.search import _extract_lavalink_error, search_tracks
from bot.music.search import is_url as _is_url
from bot.music.views import SearchView  # now from package

from .base import check_guild_and_channel, is_authorized, voice_check, MusicCogMixin

logger = logging.getLogger(__name__)


class PlaybackCog(commands.Cog, MusicCogMixin):
    def __init__(self, bot):
        self.bot = bot

    async def _check_guild_and_channel(self, ctx):
        return await check_guild_and_channel(ctx, self.bot.config)

    async def _require_authorized(self, ctx):
        return await is_authorized(ctx, self.bot)

    async def _ensure_voice(self, ctx):
        voice_channel, player = voice_check(ctx)
        if player is None:
            player = await self.bot.lavalink.get_player(ctx.guild.id, voice_channel)
        return voice_channel, player

    async def _play_track(self, ctx, player: Player, track: wavelink.Playable):
        settings = guild_settings.get(str(ctx.guild.id), self.bot.config.database_path)
        await player.set_volume(settings.get("volume", 50))
        if player.playing:
            position = self.bot.queue_manager.add(ctx.guild.id, track, ctx.author.id)
            embed = EmbedManager.track_added(
                title=track.title,
                uri=track.uri,
                position=position,
                queue_length=self.bot.queue_manager.get_length(ctx.guild.id),
                duration=track.length,
                thumbnail_url=getattr(track, "artwork_url", None),
            )
            await self._send_embed_to_response(ctx, embed, delete_after=10)
            if hasattr(self.bot, "player_messages"):
                await self.bot.player_messages.update_now_playing(ctx.guild.id)
        else:
            if hasattr(player, "store_track"):
                player.store_track(track)
            with contextlib.suppress(Exception):
                track.requester_id = ctx.author.id
            await player.play(track)
            self.bot.queue_manager.add_history(
                ctx.guild.id,
                track,
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
                    active_filter=getattr(player, "active_filter", "off"),
                )
                await self._send_embed_to_response(ctx, embed)

    async def _run_controller(self, ctx, coro):
        result = await coro
        color = discord.Color.green() if result.ok else discord.Color.red()
        await self._send_to_response(
            ctx,
            embed=discord.Embed(description=result.message, color=color),
            delete_after=8 if result.ok else 12,
        )
        if result.refresh_player and hasattr(self.bot, "player_messages"):
            await self.bot.player_messages.update_now_playing(ctx.guild.id)

    @commands.command(name="play", aliases=["p"])
    async def play(self, ctx, *, query: str):
        if not await self._check_guild_and_channel(ctx):
            return
        if not await self._require_authorized(ctx):
            return
        async with ctx.typing():
            try:
                _voice_channel, player = await self._ensure_voice(ctx)
            except (NotInVoiceChannel, DifferentVoiceChannel) as e:
                await self._send_embed_to_response(ctx, embed=build_error_embed(description=e.user_message))
                return
            if not player:
                await self._send_embed_to_response(
                    ctx,
                    embed=build_error_embed(description="Failed to connect to voice channel."),
                )
                return
            # Check if Lavalink is ready before attempting search
            if not self.bot.lavalink.is_ready:
                await self._send_embed_to_response(
                    ctx,
                    embed=build_error_embed(
                        description="❌ Lavalink is not connected. Make sure the Lavalink server is running."
                    ),
                )
                return
            try:
                settings = guild_settings.get(str(ctx.guild.id), self.bot.config.database_path)
                tracks = await search_tracks(
                    query, source=settings.get("default_source", "ytmsearch")
                )
            except Exception as e:
                logger.error("Search failed for '%s': %s", query, e)
                user_msg, _cause = _extract_lavalink_error(e)
                error_str = str(e).lower()
                # Check if it's a connection issue
                if "not connected" in error_str or "failed to connect" in error_str:
                    await self._send_embed_to_response(
                        ctx,
                        embed=build_error_embed(
                            description="❌ Lavalink is not connected. Is the Lavalink server running?"
                        ),
                    )
                elif "age" in error_str or "restricted" in error_str or "copyright" in error_str:
                    await self._send_embed_to_response(
                        ctx,
                        embed=build_error_embed(
                            description=f"❌ {user_msg} Try enabling YouTube cookies."
                        ),
                    )
                else:
                    await self._send_embed_to_response(ctx, embed=build_error_embed(description=f"❌ {user_msg}"))
                return
            if not tracks:
                embed = TrackNotFound(query).user_message
                await self._send_embed_to_response(ctx, embed=build_error_embed(description=embed))
                return
            if isinstance(tracks, wavelink.Playlist):
                await self._send_embed_to_response(
                    ctx,
                    embed=discord.Embed(
                        title="📀 Playlist Loaded",
                        description=f"Loaded **{len(tracks)}** tracks from playlist: **{tracks.name}**",
                        color=discord.Color.green(),
                    ),
                )
                for playlist_track in tracks:
                    await self._play_track(ctx, player, playlist_track)
                return
            if _is_url(query) or len(tracks) == 1:
                await self._play_track(ctx, player, tracks[0])
                return
            top_tracks = list(tracks)[:5]
            embed = EmbedManager.search_results_embed(query, top_tracks)
            view = SearchView(
                top_tracks,
                requester_id=ctx.author.id,
                bot=self.bot,
                guild_id=ctx.guild.id,
                query=query,
            )
            await self._send_to_response(ctx, embed=embed, view=view)


async def setup(bot):
    await bot.add_cog(PlaybackCog(bot))
