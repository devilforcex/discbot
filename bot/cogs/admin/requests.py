"""Access requests: requestaccess, pendingrequests, approve, deny."""

import logging

import discord
from discord.ext import commands

from bot.database.database import get_connection

from .base import log_audit, resolve_user_id

logger = logging.getLogger(__name__)


class RequestsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def _is_owner(self, ctx):
        return ctx.author.id == self.bot.config.owner_id

    async def _check_owner(self, ctx):
        if self._is_owner(ctx):
            return True
        await ctx.send("❌ You are not authorized to use this bot.")
        return False

    @commands.command(name="requestaccess")
    async def requestaccess(self, ctx):
        user_id = str(ctx.author.id)
        username = str(ctx.author.name)
        display_name = str(ctx.author.display_name)
        guild = ctx.guild.name if ctx.guild else "Unknown"
        try:
            conn = get_connection(self.bot.config.database_path)
            cur = conn.cursor()
            cur.execute("SELECT 1 FROM approved_users WHERE user_id = ?", (user_id,))
            if cur.fetchone():
                await ctx.send("✅ You are already approved.")
                return
            cur.execute(
                "SELECT 1 FROM access_requests WHERE user_id = ? AND status = 'pending'", (user_id,)
            )
            if cur.fetchone():
                await ctx.send("⏳ You already have a pending access request.")
                return
            cur.execute(
                """INSERT INTO access_requests (user_id, username, display_name, guild, status)
                   VALUES (?, ?, ?, ?, 'pending')""",
                (user_id, username, display_name, guild),
            )
            conn.commit()
        except Exception as e:
            logger.error("Failed to create access request for %s: %s", user_id, e)
            await ctx.send("❌ Failed to submit access request.")
            return
        try:
            owner = await self.bot.fetch_user(self.bot.config.owner_id)
            if owner:
                embed = discord.Embed(title="🔔 New Access Request", color=discord.Color.blue())
                embed.add_field(name="Username", value=username, inline=True)
                embed.add_field(name="Display Name", value=display_name, inline=True)
                embed.add_field(name="User ID", value=f"`{user_id}`", inline=False)
                embed.add_field(name="Guild", value=guild, inline=True)
                embed.set_footer(text="Use !approve or !deny to manage this request")
                await owner.send(embed=embed)
        except Exception as e:
            logger.warning("Failed to notify owner about access request: %s", e)
        await ctx.send("✅ Your access request has been submitted.")

    @commands.command(name="pendingrequests")
    async def pendingrequests(self, ctx):
        if not await self._check_owner(ctx):
            return
        try:
            conn = get_connection(self.bot.config.database_path)
            cur = conn.cursor()
            cur.execute("""SELECT id, user_id, username, display_name, guild, requested_at
                   FROM access_requests WHERE status = 'pending' ORDER BY requested_at""")
            rows = cur.fetchall()
        except Exception as e:
            logger.error("Failed to list pending requests: %s", e)
            await ctx.send("❌ Failed to retrieve pending requests.")
            return
        if not rows:
            await ctx.send(
                embed=discord.Embed(
                    title="📋 Pending Access Requests",
                    description="No pending requests.",
                    color=discord.Color.blue(),
                )
            )
            return
        lines = [
            f"`#{r['id']}` **{r['display_name'] or 'Unknown'}** (@{r['username'] or 'Unknown'}) — `{r['user_id']}` — {r['guild'] or 'Unknown'}"
            for r in rows
        ]
        embed = discord.Embed(
            title="📋 Pending Access Requests",
            description="\n".join(lines),
            color=discord.Color.blue(),
        )
        embed.set_footer(text=f"Total: {len(rows)} pending request(s)")
        await ctx.send(embed=embed)

    @commands.command(name="approve")
    async def approve(self, ctx, *, user_input: str):
        if not await self._check_owner(ctx):
            return
        user_id = resolve_user_id(user_input)
        if not user_id:
            await ctx.send("❌ Invalid user ID or mention.")
            return
        try:
            conn = get_connection(self.bot.config.database_path)
            cur = conn.cursor()
            cur.execute(
                "SELECT username, display_name FROM access_requests WHERE user_id = ? AND status = 'pending'",
                (user_id,),
            )
            row = cur.fetchone()
            username = row["username"] if row else "Unknown"
            display_name = row["display_name"] if row else "Unknown"
            cur.execute(
                "UPDATE access_requests SET status = 'approved' WHERE user_id = ? AND status = 'pending'",
                (user_id,),
            )
            cur.execute(
                """INSERT OR IGNORE INTO approved_users (user_id, username, display_name, added_by)
                   VALUES (?, ?, ?, ?)""",
                (user_id, username, display_name, str(ctx.author.id)),
            )
            conn.commit()
        except Exception as e:
            logger.error("Failed to approve user %s: %s", user_id, e)
            await ctx.send("❌ Failed to approve user.")
            return
        await log_audit(
            "approve", user_id, username, str(ctx.author.id), self.bot.config.database_path
        )
        await ctx.send("✅ User approved successfully.")

    @commands.command(name="deny")
    async def deny(self, ctx, *, user_input: str):
        if not await self._check_owner(ctx):
            return
        user_id = resolve_user_id(user_input)
        if not user_id:
            await ctx.send("❌ Invalid user ID or mention.")
            return
        try:
            conn = get_connection(self.bot.config.database_path)
            cur = conn.cursor()
            cur.execute(
                "SELECT username, display_name FROM access_requests WHERE user_id = ? AND status = 'pending'",
                (user_id,),
            )
            row = cur.fetchone()
            username = row["username"] if row else "Unknown"
            cur.execute(
                "UPDATE access_requests SET status = 'denied' WHERE user_id = ? AND status = 'pending'",
                (user_id,),
            )
            conn.commit()
        except Exception as e:
            logger.error("Failed to deny request for %s: %s", user_id, e)
            await ctx.send("❌ Failed to deny request.")
            return
        await log_audit(
            "deny", user_id, username, str(ctx.author.id), self.bot.config.database_path
        )
        await ctx.send("✅ Request denied.")


async def setup(bot):
    await bot.add_cog(RequestsCog(bot))
