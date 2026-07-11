"""Misc admin: whoami, status, 247."""
import logging
import discord
from discord.ext import commands

from bot.database.database import get_connection
from bot.core.services.auth import check_authorized

logger = logging.getLogger(__name__)


class MiscAdminCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def _is_owner(self, ctx):
        return ctx.author.id == self.bot.config.owner_id

    async def _check_owner(self, ctx):
        if self._is_owner(ctx):
            return True
        await ctx.send("❌ You are not authorized to use this bot.")
        return False

    @commands.command(name="whoami")
    async def whoami(self, ctx):
        user_id = str(ctx.author.id)
        username = str(ctx.author.name)
        display_name = str(ctx.author.display_name)
        guild = ctx.guild.name if ctx.guild else "N/A"
        channel = ctx.channel.name if ctx.channel else "N/A"

        allowed, _ = check_authorized(ctx.author.id, self.bot.config.owner_id, self.bot.config.database_path)
        is_blacklisted = False
        try:
            conn = get_connection(self.bot.config.database_path)
            cur = conn.cursor()
            cur.execute("SELECT 1 FROM blacklisted_users WHERE user_id = ?", (user_id,))
            is_blacklisted = cur.fetchone() is not None
        except Exception:
            pass

        embed = discord.Embed(
            title="👤 User Info",
            color=discord.Color.green() if allowed else discord.Color.red(),
        )
        embed.add_field(name="Username", value=f"@{username}", inline=True)
        embed.add_field(name="Display Name", value=display_name, inline=True)
        embed.add_field(name="User ID", value=f"`{user_id}`", inline=False)
        embed.add_field(name="Guild", value=guild, inline=True)
        embed.add_field(name="Channel", value=channel, inline=True)
        embed.add_field(name="Access Status", value="✅ Authorized" if allowed else "❌ Not Authorized", inline=False)
        embed.add_field(name="Blacklist Status", value="🚫 Blacklisted" if is_blacklisted else "✅ Not Blacklisted", inline=False)
        await ctx.send(embed=embed)

    @commands.command(name="status")
    async def status(self, ctx):
        config = self.bot.config
        lavalink_status = "Disconnected"
        try:
            import wavelink
            node = wavelink.Pool.get_node()
            if node and getattr(node, "is_connected", False):
                lavalink_status = f"Connected ({round(node.latency)}ms)"
        except Exception:
            pass

        guild_id = config.guild_id
        queue_length = self.bot.queue_manager.get_length(guild_id)
        current_track = "None"
        player = discord.utils.get(self.bot.voice_clients, guild__id=guild_id)
        if player and (getattr(player, "playing", False) or getattr(player, "paused", False)) and player.last_track:
            current_track = player.last_track.title

        uptime = "N/A"
        if hasattr(self.bot, "get_uptime"):
            uptime = await self.bot.get_uptime()

        embed = discord.Embed(title="🤖 Bot Status", color=discord.Color.green())
        embed.add_field(name="Guild ID", value=f"`{config.guild_id}`", inline=True)
        embed.add_field(name="Music Channel ID", value=f"`{config.music_channel_id}`", inline=True)
        embed.add_field(name="Lavalink Status", value=lavalink_status, inline=False)
        embed.add_field(name="Queue Length", value=str(queue_length), inline=True)
        embed.add_field(name="Current Track", value=current_track or "None", inline=True)
        embed.add_field(name="Bot Uptime", value=uptime, inline=False)
        await ctx.send(embed=embed)

    @commands.command(name="247")
    async def toggle_247(self, ctx, *, state: str):
        if not await self._check_owner(ctx):
            return
        state_lower = state.strip().lower()
        if state_lower not in ("on", "off"):
            await ctx.send("❌ Usage: `!247 on` or `!247 off`")
            return
        value = "true" if state_lower == "on" else "false"
        try:
            conn = get_connection(self.bot.config.database_path)
            cur = conn.cursor()
            cur.execute("INSERT OR REPLACE INTO bot_settings (key, value) VALUES ('247_enabled', ?)", (value,))
            conn.commit()
        except Exception as e:
            logger.error("Failed to update 24/7 setting: %s", e)
            await ctx.send("❌ Failed to update 24/7 mode.")
            return
        status_text = "enabled" if state_lower == "on" else "disabled"
        await ctx.send(f"✅ 24/7 mode {status_text}.")


async def setup(bot):
    await bot.add_cog(MiscAdminCog(bot))
