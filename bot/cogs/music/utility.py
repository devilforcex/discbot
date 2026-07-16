"""Utility cog — ping, help."""

import discord
import wavelink
from discord.ext import commands

from .base import MusicCogMixin, check_guild_and_channel, is_authorized


class UtilityCog(commands.Cog, MusicCogMixin):
    def __init__(self, bot):
        self.bot = bot

    async def _check_guild_and_channel(self, ctx):
        return await check_guild_and_channel(ctx, self.bot.config)

    async def _require_authorized(self, ctx):
        return await is_authorized(ctx, self.bot)

    @commands.command(name="ping")
    async def ping(self, ctx):
        if not await self._check_guild_and_channel(ctx):
            return
        if not await self._require_authorized(ctx):
            return
        bot_latency = round(self.bot.latency * 1000)
        lavalink_latency = "N/A"
        lavalink_status = "Disconnected"
        node_info = "No node"
        try:
            node = wavelink.Pool.get_node()
            if node:
                if getattr(node, "is_connected", False):
                    lavalink_latency = f"{round(node.latency)}ms"
                    lavalink_status = "Connected"
                    node_info = f"{node.identifier}"
                else:
                    lavalink_status = "Connecting..."
        except Exception:
            pass
        embed = discord.Embed(title="🏓 Pong!", color=discord.Color.green())
        embed.add_field(name="Bot Latency", value=f"{bot_latency}ms", inline=True)
        embed.add_field(name="Lavalink Status", value=lavalink_status, inline=True)
        embed.add_field(name="Lavalink Latency", value=lavalink_latency, inline=True)
        embed.add_field(name="Node", value=node_info, inline=True)
        await self._send_embed_to_response(ctx, embed)

    @commands.command(name="help")
    async def help_command(self, ctx, *, command: str | None = None):
        if not await self._check_guild_and_channel(ctx):
            return
        from bot.music.help.categories import CATEGORIES
        from bot.music.help_views import HelpView, build_category_embed, build_main_help_embed

        support_url = getattr(self.bot.config, "support_server_url", None) or getattr(
            self.bot.config, "discord_invite_url", None
        )
        invite_url = getattr(self.bot.config, "bot_invite_url", None)
        vote_url = getattr(self.bot.config, "website_url", None)

        key = (command or "").strip().lower()
        label_to_key = {cat["label"].lower(): name for name, cat in CATEGORIES.items()}
        category_key = key if key in CATEGORIES else label_to_key.get(key)
        embed = (
            build_category_embed(category_key, self.bot.user)
            if category_key
            else build_main_help_embed(bot_user=self.bot.user)
        )
        view = HelpView(
            bot=self.bot, support_url=support_url, invite_url=invite_url, vote_url=vote_url
        )
        await self._send_to_response(ctx, embed=embed, view=view)


async def setup(bot):
    await bot.add_cog(UtilityCog(bot))
