"""Queue cog — queue, nowplaying, shuffle, loop, autoplay, volume."""

import logging

import discord
from discord.ext import commands

from bot.core.errors import DifferentVoiceChannel, NotInVoiceChannel, build_error_embed
from bot.music.embed_manager import EmbedManager
from bot.music.emoji import EMOJI
from bot.music.queue_manager import LoopMode
from bot.music.views import QueuePaginatorView

from .base import (
    MusicCogMixin,
    check_guild_and_channel,
    get_player_from_ctx,
    is_authorized,
    voice_check,
)

logger = logging.getLogger(__name__)


class QueueCog(commands.Cog, MusicCogMixin):
    def __init__(self, bot):
        self.bot = bot

    async def _check_guild_and_channel(self, ctx):
        return await check_guild_and_channel(ctx, self.bot.config)

    async def _require_authorized(self, ctx):
        return await is_authorized(ctx, self.bot)

    async def _run_controller(self, ctx, coro):
        result = await coro
        color = discord.Color.green() if result.ok else discord.Color.red()
        await self._send_embed_to_response(
            ctx,
            embed=discord.Embed(description=result.message, color=color),
            delete_after=8 if result.ok else 12,
        )
        if result.refresh_player and hasattr(self.bot, "player_messages"):
            await self.bot.player_messages.update_now_playing(ctx.guild.id)

    @commands.command(name="queue", aliases=["q"])
    async def queue(self, ctx, page: int = 1):
        if not await self._check_guild_and_channel(ctx):
            return
        if not await self._require_authorized(ctx):
            return
        player = get_player_from_ctx(ctx)
        current_track = None
        if (
            player
            and (getattr(player, "playing", False) or getattr(player, "paused", False))
            and player.last_track
        ):
            current_track = {
                "title": player.last_track.title,
                "author": player.last_track.author,
                "uri": player.last_track.uri,
                "length": player.last_track.length,
                "requester_id": getattr(player.last_track, "requester_id", ctx.author.id),
            }
        queue_list = self.bot.queue_manager.get_all_as_dicts(ctx.guild.id)
        if not queue_list and not current_track:
            await self._send_embed_to_response(
                ctx, embed=build_error_embed(description="The queue is empty.")
            )
            return
        embed = EmbedManager.queue_embed(
            queue=queue_list,
            current_track=current_track,
            page=page,
            guild_name=ctx.guild.name if ctx.guild else "Server",
        )
        view = QueuePaginatorView(
            bot=self.bot,
            guild_id=ctx.guild.id,
            requester_id=ctx.author.id,
            guild_name=ctx.guild.name if ctx.guild else "Server",
            page=page,
        )
        await self._send_to_response(ctx, embed=embed, view=view)

    @commands.command(name="nowplaying", aliases=["np", "current"])
    async def nowplaying(self, ctx):
        if not await self._check_guild_and_channel(ctx):
            return
        if not await self._require_authorized(ctx):
            return
        if hasattr(self.bot, "player_messages"):
            # Use music channel for player message
            music_channel = await self._get_response_channel(ctx)
            msg = await self.bot.player_messages.ensure_message(ctx.guild.id, channel=music_channel)
            await self.bot.player_messages.update_now_playing(ctx.guild.id)
            if msg:
                await self._send_to_response(
                    ctx,
                    content=f"{EMOJI['music']} Player updated — use buttons + filter dropdown.",
                    delete_after=6,
                )
            else:
                await self._send_embed_to_response(
                    ctx, embed=build_error_embed(description="Could not create player message.")
                )
            return
        player = get_player_from_ctx(ctx)
        if not player or not player.playing or not player.last_track:
            await self._send_embed_to_response(
                ctx, embed=build_error_embed(description="Nothing is currently playing.")
            )
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
            active_filter=getattr(player, "active_filter", "off"),
        )
        await self._send_embed_to_response(ctx, embed=embed)

    @commands.command(name="shuffle")
    async def shuffle(self, ctx):
        if not await self._check_guild_and_channel(ctx):
            return
        if not await self._require_authorized(ctx):
            return
        await self._run_controller(
            ctx, self.bot.player_controller.shuffle(ctx.guild.id, ctx.author)
        )

    @commands.command(name="loop")
    async def loop(self, ctx, mode: str = "none"):
        if not await self._check_guild_and_channel(ctx):
            return
        if not await self._require_authorized(ctx):
            return
        mode_lower = mode.strip().lower()
        if mode_lower not in ("none", "track", "queue"):
            await self._send_embed_to_response(
                ctx,
                embed=build_error_embed(description="Invalid mode. Use: none, track, or queue."),
            )
            return
        try:
            _, player = voice_check(ctx)
        except (NotInVoiceChannel, DifferentVoiceChannel) as e:
            await self._send_embed_to_response(
                ctx, embed=build_error_embed(description=e.user_message)
            )
            return
        if not player:
            await self._send_embed_to_response(
                ctx, embed=build_error_embed(description="No active music session.")
            )
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
        await self._send_embed_to_response(ctx, embed=embed)
        if hasattr(self.bot, "player_messages"):
            await self.bot.player_messages.update_now_playing(ctx.guild.id)

    @commands.command(name="autoplay")
    async def autoplay(self, ctx, state: str = "toggle"):
        if not await self._check_guild_and_channel(ctx):
            return
        if not await self._require_authorized(ctx):
            return
        try:
            _, player = voice_check(ctx)
        except (NotInVoiceChannel, DifferentVoiceChannel) as e:
            await self._send_embed_to_response(
                ctx, embed=build_error_embed(description=e.user_message)
            )
            return
        if not player:
            await self._send_embed_to_response(
                ctx, embed=build_error_embed(description="No active music session.")
            )
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
        await self._send_embed_to_response(ctx, embed=embed)

    @commands.command(name="volume", aliases=["vol", "v"])
    async def volume(self, ctx, volume: int = 50):
        if not await self._check_guild_and_channel(ctx):
            return
        if not await self._require_authorized(ctx):
            return
        if volume < 0 or volume > 100:
            await self._send_embed_to_response(
                ctx, embed=build_error_embed(description="Volume must be between 0 and 100.")
            )
            return
        await self._run_controller(
            ctx, self.bot.player_controller.set_volume(ctx.guild.id, ctx.author, volume)
        )


async def setup(bot):
    await bot.add_cog(QueueCog(bot))
