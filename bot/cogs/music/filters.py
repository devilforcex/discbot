"""Filters & seek cog."""

import contextlib
import logging

import discord
from discord.ext import commands

from bot.core.errors import build_error_embed
from bot.music.audio_filters import get_filter_choices
from bot.music.embed_manager import EmbedManager

from .base import check_guild_and_channel, get_player_from_ctx, is_authorized, MusicCogMixin

logger = logging.getLogger(__name__)


class FilterSelectView(discord.ui.View):
    """View for !filters command — dropdown to apply filter."""

    def __init__(self, bot, guild_id: int, requester_id: int, active_filter: str = "off"):
        super().__init__(timeout=60)
        self.bot = bot
        self.guild_id = guild_id
        self.requester_id = requester_id
        self.active_filter = active_filter

        options = []
        for value, label, desc, emoji in get_filter_choices():
            is_active = value == active_filter
            desc_display = (desc + (" (active)" if is_active else ""))[:100]
            options.append(
                discord.SelectOption(
                    label=label[:100],
                    description=desc_display,
                    value=value,
                    emoji=emoji,
                    default=is_active,
                )
            )

        select = discord.ui.Select(
            placeholder="Select A Filter To Apply.",
            min_values=1,
            max_values=1,
            options=options[:25],
            row=0,
        )
        select.callback = self.select_callback
        self.add_item(select)

    async def select_callback(self, interaction: discord.Interaction):
        from bot.music.player_controller import PlayerController

        controller = getattr(self.bot, "player_controller", None)
        if controller is None:
            controller = PlayerController(self.bot)
            self.bot.player_controller = controller

        ok, err = controller.check_authorized(interaction.user.id)
        if not ok:
            await interaction.response.send_message(err, ephemeral=True)
            return

        filter_name = interaction.data.get("values", [""])[0]  # type: ignore[attr-defined]
        await interaction.response.defer(ephemeral=True)

        guild = self.bot.get_guild(self.guild_id)
        member = guild.get_member(interaction.user.id) if guild else None
        if not member:
            member = interaction.guild.get_member(interaction.user.id) if interaction.guild else None
        if not member:
            member = interaction.user  # type: ignore[assignment]

        result = await controller.set_filter(self.guild_id, member, filter_name)  # type: ignore[arg-type]
        await interaction.followup.send(result.message, ephemeral=True)

        if result.refresh_player and hasattr(self.bot, "player_messages"):
            with contextlib.suppress(Exception):
                await self.bot.player_messages.update_now_playing(self.guild_id)

        try:
            embed = EmbedManager.filter_embed(
                active_filter=filter_name if filter_name != "reset" else "off"
            )
            await interaction.message.edit(embed=embed, view=self)
        except Exception:
            pass

    @discord.ui.button(label="Reset", style=discord.ButtonStyle.secondary, emoji="🔄", row=1)
    async def reset_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        from bot.music.player_controller import PlayerController

        controller = getattr(self.bot, "player_controller", None)
        if controller is None:
            controller = PlayerController(self.bot)
            self.bot.player_controller = controller

        ok, err = controller.check_authorized(interaction.user.id)
        if not ok:
            await interaction.response.send_message(err, ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)
        guild = self.bot.get_guild(self.guild_id)
        member = guild.get_member(interaction.user.id) if guild else None
        if not member:
            member = interaction.guild.get_member(interaction.user.id) if interaction.guild else None
        if not member:
            member = interaction.user  # type: ignore[assignment]

        result = await controller.set_filter(self.guild_id, member, "reset")  # type: ignore[arg-type]
        await interaction.followup.send(result.message, ephemeral=True)
        if hasattr(self.bot, "player_messages"):
            with contextlib.suppress(Exception):
                await self.bot.player_messages.update_now_playing(self.guild_id)
        try:
            embed = EmbedManager.filter_embed(active_filter="off")
            await interaction.message.edit(embed=embed, view=self)
        except Exception:
            pass

    @discord.ui.button(label="Close", style=discord.ButtonStyle.danger, emoji="❌", row=1)
    async def close_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        for child in self.children:
            child.disabled = True
        self.stop()
        try:
            await interaction.message.delete()
        except Exception:
            with contextlib.suppress(Exception):
                await interaction.response.edit_message(view=self)


class FiltersCog(commands.Cog, MusicCogMixin):
    def __init__(self, bot):
        self.bot = bot

    async def _check_guild_and_channel(self, ctx):
        return await check_guild_and_channel(ctx, self.bot.config)

    async def _require_authorized(self, ctx):
        return await is_authorized(ctx, self.bot)

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

    @commands.command(name="seek", aliases=["seekto"])
    async def seek(self, ctx, seconds: int):
        if not await self._check_guild_and_channel(ctx):
            return
        if not await self._require_authorized(ctx):
            return
        player = get_player_from_ctx(ctx)
        if not player or not player.playing:
            await self._send_embed_to_response(ctx, embed=build_error_embed(description="Nothing is currently playing."))
            return
        try:
            ms = seconds * 1000
            await player.seek(ms)
            await self._send_embed_to_response(
                ctx,
                embed=discord.Embed(
                    description=f"⏩ Seeked to `{EmbedManager._format_duration(ms)}`.",
                    color=discord.Color.green(),
                ),
            )
        except Exception as e:
            await self._send_embed_to_response(ctx, embed=build_error_embed(description=f"Seek failed: {e}"))

    @commands.command(name="forward", aliases=["fwd", "seekfwd"])
    async def forward(self, ctx, seconds: int = 10):
        if not await self._check_guild_and_channel(ctx):
            return
        if not await self._require_authorized(ctx):
            return
        await self._run_controller(
            ctx, self.bot.player_controller.seek_forward(ctx.guild.id, ctx.author, seconds)
        )

    @commands.command(name="rewind", aliases=["rew", "seekback"])
    async def rewind(self, ctx, seconds: int = 10):
        if not await self._check_guild_and_channel(ctx):
            return
        if not await self._require_authorized(ctx):
            return
        await self._run_controller(
            ctx, self.bot.player_controller.seek_backward(ctx.guild.id, ctx.author, seconds)
        )

    @commands.command(name="replay", aliases=["restart"])
    async def replay(self, ctx):
        if not await self._check_guild_and_channel(ctx):
            return
        if not await self._require_authorized(ctx):
            return
        await self._run_controller(ctx, self.bot.player_controller.replay(ctx.guild.id, ctx.author))

    @commands.command(name="filter", aliases=["filterset", "audiofilter"])
    async def filter_cmd(self, ctx, *, filter_name: str = "off"):
        if not await self._check_guild_and_channel(ctx):
            return
        if not await self._require_authorized(ctx):
            return
        await self._run_controller(
            ctx, self.bot.player_controller.set_filter(ctx.guild.id, ctx.author, filter_name)
        )

    @commands.command(name="filters", aliases=["filterlist", "listfilters"])
    async def filters(self, ctx):
        if not await self._check_guild_and_channel(ctx):
            return
        if not await self._require_authorized(ctx):
            return
        player = get_player_from_ctx(ctx)
        active = getattr(player, "active_filter", "off") if player else "off"
        embed = EmbedManager.filter_embed(active_filter=active)
        view = FilterSelectView(
            bot=self.bot, guild_id=ctx.guild.id, requester_id=ctx.author.id, active_filter=active
        )
        await self._send_to_response(ctx, embed=embed, view=view)


async def setup(bot):
    await bot.add_cog(FiltersCog(bot))
