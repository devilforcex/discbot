"""Utility cog — ping, help."""
import discord
import wavelink
from discord.ext import commands

from .base import check_guild_and_channel, is_authorized


class UtilityCog(commands.Cog):
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
        lavalink_sources = "Unknown"
        try:
            node = wavelink.Pool.get_node()
            if node:
                if getattr(node, "is_connected", False):
                    lavalink_latency = f"{round(node.latency)}ms"
                    lavalink_status = "Connected"
                    node_info = f"{node.identifier}"
                    # Try to get available sources from Lavalink
                    try:
                        import aiohttp
                        async with aiohttp.ClientSession() as session:
                            info_url = f"{node.uri.replace('ws', 'http').replace('wss', 'https')}/info"
                            headers = {"Authorization": node.password} if hasattr(node, 'password') else {}
                            async with session.get(info_url, headers=headers, timeout=aiohttp.ClientTimeout(total=5)) as resp:
                                if resp.status == 200:
                                    import json
                                    info = await resp.json()
                                    sources = info.get("sourceManagers", [])
                                    lavalink_sources = ", ".join(sources) if sources else "None"
                                    # Check for YouTube source
                                    has_yt = any("youtube" in s.lower() for s in sources)
                                    if not has_yt:
                                        lavalink_sources += " ⚠️ **YouTube source missing!**"
                    except Exception:
                        lavalink_sources = "Could not fetch"
                else:
                    lavalink_status = "Connecting..."
        except Exception:
            pass
        embed = discord.Embed(title="🏓 Pong!", color=discord.Color.green())
        embed.add_field(name="Bot Latency", value=f"{bot_latency}ms", inline=True)
        embed.add_field(name="Lavalink Status", value=lavalink_status, inline=True)
        embed.add_field(name="Lavalink Latency", value=lavalink_latency, inline=True)
        embed.add_field(name="Node", value=node_info, inline=True)
        embed.add_field(name="Lavalink Sources", value=lavalink_sources, inline=False)
        
        # Add troubleshooting tip if YouTube source is missing
        if "YouTube source missing" in lavalink_sources:
            embed.add_field(
                name="⚠️ Troubleshooting",
                value="YouTube source not detected in Lavalink. This causes 'Something went wrong while looking up the track' errors.\n"
                      "Fix: Ensure `application.yml` has the YouTube plugin:\n"
                      "`plugins:\n  - dependency: \"dev.lavalink.youtube:youtube-plugin:1.18.0\"`",
                inline=False
            )
        await ctx.send(embed=embed)

    @commands.command(name="help")
    async def help_command(self, ctx, *, command: str = None):
        if not await self._check_guild_and_channel(ctx):
            return
        from bot.music.help_views import HelpView, build_category_embed, build_main_help_embed
        from bot.music.help.categories import CATEGORIES

        support_url = getattr(self.bot.config, "support_server_url", None) or getattr(
            self.bot.config, "discord_invite_url", None
        )
        invite_url = getattr(self.bot.config, "bot_invite_url", None)
        vote_url = getattr(self.bot.config, "website_url", None)

        key = (command or "").strip().lower()
        label_to_key = {cat["label"].lower(): name for name, cat in CATEGORIES.items()}
        category_key = key if key in CATEGORIES else label_to_key.get(key)
        embed = build_category_embed(category_key, self.bot.user) if category_key else build_main_help_embed(bot_user=self.bot.user)
        view = HelpView(bot=self.bot, support_url=support_url, invite_url=invite_url, vote_url=vote_url)
        await ctx.send(embed=embed, view=view)


async def setup(bot):
    await bot.add_cog(UtilityCog(bot))
