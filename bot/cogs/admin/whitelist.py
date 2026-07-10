"""Whitelist management."""
import logging
import discord
from discord.ext import commands

from bot.database.database import get_connection
from .base import resolve_user_id, log_audit

logger = logging.getLogger(__name__)


class WhitelistCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def _is_owner(self, ctx) -> bool:
        return ctx.author.id == self.bot.config.owner_id

    async def _check_owner(self, ctx) -> bool:
        if self._is_owner(ctx):
            return True
        await ctx.send("❌ You are not authorized to use this bot.")
        return False

    @commands.command(name="adduser")
    async def adduser(self, ctx, *, user_input: str):
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
                """INSERT OR IGNORE INTO approved_users (user_id, username, display_name, added_by)
                   VALUES (?, ?, ?, ?)""",
                (user_id, username, display_name, str(ctx.author.id)),
            )
            conn.commit()
        except Exception as e:
            logger.error("Failed to add user %s: %s", user_id, e)
            await ctx.send("❌ Failed to add user.")
            return
        await log_audit("adduser", user_id, username, str(ctx.author.id), self.bot.config.database_path)
        await ctx.send("✅ User added successfully.")

    @commands.command(name="removeuser")
    async def removeuser(self, ctx, *, user_input: str):
        if not await self._check_owner(ctx):
            return
        user_id = resolve_user_id(user_input)
        if not user_id:
            await ctx.send("❌ Invalid user ID or mention.")
            return
        try:
            conn = get_connection(self.bot.config.database_path)
            cur = conn.cursor()
            cur.execute("SELECT username, display_name FROM approved_users WHERE user_id = ?", (user_id,))
            row = cur.fetchone()
            target_username = row["username"] if row else "Unknown"
            cur.execute("DELETE FROM approved_users WHERE user_id = ?", (user_id,))
            conn.commit()
        except Exception as e:
            logger.error("Failed to remove user %s: %s", user_id, e)
            await ctx.send("❌ Failed to remove user.")
            return
        await log_audit("removeuser", user_id, target_username, str(ctx.author.id), self.bot.config.database_path)
        await ctx.send("✅ User removed successfully.")

    @commands.command(name="listusers")
    async def listusers(self, ctx):
        if not await self._check_owner(ctx):
            return
        try:
            conn = get_connection(self.bot.config.database_path)
            cur = conn.cursor()
            cur.execute("SELECT user_id, username, display_name, added_at FROM approved_users ORDER BY added_at")
            rows = cur.fetchall()
        except Exception as e:
            logger.error("Failed to list users: %s", e)
            await ctx.send("❌ Failed to retrieve user list.")
            return
        if not rows:
            await ctx.send(embed=discord.Embed(title="👥 Approved Users", description="No approved users.", color=discord.Color.blue()))
            return
        lines = [f"• **{r['display_name'] or 'Unknown'}** (@{r['username'] or 'Unknown'}) — `{r['user_id']}`" for r in rows]
        embed = discord.Embed(title="👥 Approved Users", description="\n".join(lines), color=discord.Color.blue())
        embed.set_footer(text=f"Total: {len(rows)} user(s)")
        await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(WhitelistCog(bot))
