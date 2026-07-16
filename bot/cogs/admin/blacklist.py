"""Blacklist management."""

import logging

from discord.ext import commands

from bot.database.database import get_connection

from .base import log_audit, resolve_user_id

logger = logging.getLogger(__name__)


class BlacklistCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def _is_owner(self, ctx):
        return ctx.author.id == self.bot.config.owner_id

    async def _check_owner(self, ctx):
        if self._is_owner(ctx):
            return True
        await ctx.send("❌ You are not authorized to use this bot.")
        return False

    @commands.command(name="blacklist")
    async def blacklist(self, ctx, *, user_input: str):
        if not await self._check_owner(ctx):
            return
        user_id = resolve_user_id(user_input)
        if not user_id:
            await ctx.send("❌ Invalid user ID or mention.")
            return
        username = "Unknown"
        display_name = "Unknown"
        if ctx.guild:
            member = ctx.guild.get_member(int(user_id))
            if member:
                username = str(member.name)
                display_name = str(member.display_name)
        try:
            conn = get_connection(self.bot.config.database_path)
            cur = conn.cursor()
            cur.execute(
                """INSERT OR IGNORE INTO blacklisted_users (user_id, username, display_name, added_by)
                   VALUES (?, ?, ?, ?)""",
                (user_id, username, display_name, str(ctx.author.id)),
            )
            conn.commit()
        except Exception as e:
            logger.error("Failed to blacklist user %s: %s", user_id, e)
            await ctx.send("❌ Failed to blacklist user.")
            return
        await log_audit(
            "blacklist", user_id, username, str(ctx.author.id), self.bot.config.database_path
        )
        await ctx.send("✅ User blacklisted.")

    @commands.command(name="unblacklist")
    async def unblacklist(self, ctx, *, user_input: str):
        if not await self._check_owner(ctx):
            return
        user_id = resolve_user_id(user_input)
        if not user_id:
            await ctx.send("❌ Invalid user ID or mention.")
            return
        try:
            conn = get_connection(self.bot.config.database_path)
            cur = conn.cursor()
            cur.execute("SELECT username FROM blacklisted_users WHERE user_id = ?", (user_id,))
            row = cur.fetchone()
            target_username = row["username"] if row else "Unknown"
            cur.execute("DELETE FROM blacklisted_users WHERE user_id = ?", (user_id,))
            conn.commit()
        except Exception as e:
            logger.error("Failed to unblacklist user %s: %s", user_id, e)
            await ctx.send("❌ Failed to unblacklist user.")
            return
        await log_audit(
            "unblacklist",
            user_id,
            target_username,
            str(ctx.author.id),
            self.bot.config.database_path,
        )
        await ctx.send("✅ User unblacklisted.")


async def setup(bot):
    await bot.add_cog(BlacklistCog(bot))
