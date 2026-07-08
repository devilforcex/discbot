"""
Admin commands cog for the Discord Music Bot.
Manages the access control system: whitelist, blacklist,
access requests, audit logging, 24/7 mode, and status.
"""

import logging
from typing import Optional

import discord
from discord.ext import commands

from bot.database.database import get_connection

logger = logging.getLogger(__name__)


def _resolve_user_id(user_input: str) -> Optional[str]:
    """Resolve a Discord user ID from a raw string or mention.

    Handles formats:
    - Raw ID: 123456789012345678
    - Mention: <@123456789012345678>
    - Nickname mention: <@!123456789012345678>

    Args:
        user_input: The user-provided input string.

    Returns:
        The resolved user ID string, or None if invalid.
    """
    stripped = user_input.strip()

    # Handle mention format <@123> or <@!123>
    if stripped.startswith("<@") and stripped.endswith(">"):
        inner = stripped[2:-1]
        if inner.startswith("!"):
            inner = inner[1:]
        if inner.isdigit():
            return inner
        return None

    # Handle raw numeric ID
    if stripped.isdigit():
        return stripped

    return None


class AdminCommands(commands.Cog):
    """Owner-only commands for managing bot access control, whitelist, blacklist, and 24/7 mode."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # ============================================================
    # Authorization Helpers
    # ============================================================

    def _is_owner(self, ctx: commands.Context) -> bool:
        """Check if the command author is the bot owner."""
        return ctx.author.id == self.bot.config.owner_id

    async def _check_owner(self, ctx: commands.Context) -> bool:
        """Verify the user is the owner. Send error if not."""
        if self._is_owner(ctx):
            return True
        await ctx.send("❌ You are not authorized to use this bot.")
        return False

    async def _is_authorized(self, ctx: commands.Context) -> bool:
        """Check authorization in order: owner > blacklist > whitelist > deny.

        Returns True if the user is authorized to use the bot.
        Returns False and sends an appropriate message if not.
        """
        # 1. Owner always passes
        if self._is_owner(ctx):
            return True

        user_id = str(ctx.author.id)

        try:
            conn = get_connection(self.bot.config.database_path)
            cursor = conn.cursor()

            # 2. Check blacklist
            cursor.execute(
                "SELECT 1 FROM blacklisted_users WHERE user_id = ?",
                (user_id,),
            )
            if cursor.fetchone():
                await ctx.send("❌ You are blacklisted.")
                return False

            # 3. Check whitelist (approved_users)
            cursor.execute(
                "SELECT 1 FROM approved_users WHERE user_id = ?",
                (user_id,),
            )
            if cursor.fetchone():
                return True

        except Exception as e:
            logger.error("Authorization check failed for user %s: %s", user_id, e)

        # 4. Deny
        await ctx.send("❌ You are not authorized to use this bot.")
        return False

    async def _require_authorized(self, ctx: commands.Context) -> bool:
        """Wrapper that returns bool for command gating."""
        return await self._is_authorized(ctx)

    async def _log_audit(
        self,
        action: str,
        target_user_id: str,
        target_username: str,
        moderator_id: str,
    ) -> None:
        """Insert an audit log entry."""
        try:
            conn = get_connection(self.bot.config.database_path)
            cursor = conn.cursor()
            cursor.execute(
                """INSERT INTO audit_logs (action, target_user_id, target_username, moderator_id)
                   VALUES (?, ?, ?, ?)""",
                (action, target_user_id, target_username, moderator_id),
            )
            conn.commit()
            logger.info(
                "Audit: %s | target=%s (%s) | moderator=%s",
                action, target_username, target_user_id, moderator_id,
            )
        except Exception as e:
            logger.error("Failed to write audit log: %s", e)

    # ============================================================
    # Whitelist Management
    # ============================================================

    @commands.command(name="adduser")
    async def adduser(self, ctx: commands.Context, *, user_input: str) -> None:
        """Add a user to the approved users list.

        Usage: !adduser <user_id_or_mention>
        Example: !adduser @User or !adduser 123456789
        """
        if not await self._check_owner(ctx):
            return

        user_id = _resolve_user_id(user_input)
        if not user_id:
            await ctx.send("❌ Invalid user ID or mention.")
            return

        # Try to get username/display_name from guild if user is present
        username = "Unknown"
        display_name = "Unknown"
        if ctx.guild:
            member = ctx.guild.get_member(int(user_id))
            if member:
                username = str(member.name)
                display_name = str(member.display_name)

        try:
            conn = get_connection(self.bot.config.database_path)
            cursor = conn.cursor()
            cursor.execute(
                """INSERT OR IGNORE INTO approved_users (user_id, username, display_name, added_by)
                   VALUES (?, ?, ?, ?)""",
                (user_id, username, display_name, str(ctx.author.id)),
            )
            conn.commit()
        except Exception as e:
            logger.error("Failed to add user %s: %s", user_id, e)
            await ctx.send("❌ Failed to add user.")
            return

        await self._log_audit("adduser", user_id, username, str(ctx.author.id))
        await ctx.send("✅ User added successfully.")

    @commands.command(name="removeuser")
    async def removeuser(self, ctx: commands.Context, *, user_input: str) -> None:
        """Remove a user from the approved users list.

        Usage: !removeuser <user_id_or_mention>
        Example: !removeuser @User or !removeuser 123456789
        """
        if not await self._check_owner(ctx):
            return

        user_id = _resolve_user_id(user_input)
        if not user_id:
            await ctx.send("❌ Invalid user ID or mention.")
            return

        try:
            conn = get_connection(self.bot.config.database_path)
            cursor = conn.cursor()
            cursor.execute(
                "SELECT username, display_name FROM approved_users WHERE user_id = ?",
                (user_id,),
            )
            row = cursor.fetchone()
            target_username = row["username"] if row else "Unknown"

            cursor.execute(
                "DELETE FROM approved_users WHERE user_id = ?",
                (user_id,),
            )
            conn.commit()
        except Exception as e:
            logger.error("Failed to remove user %s: %s", user_id, e)
            await ctx.send("❌ Failed to remove user.")
            return

        await self._log_audit("removeuser", user_id, target_username, str(ctx.author.id))
        await ctx.send("✅ User removed successfully.")

    @commands.command(name="listusers")
    async def listusers(self, ctx: commands.Context) -> None:
        """List all approved users with username, display name, and user ID.

        Usage: !listusers
        """
        if not await self._check_owner(ctx):
            return

        try:
            conn = get_connection(self.bot.config.database_path)
            cursor = conn.cursor()
            cursor.execute(
                "SELECT user_id, username, display_name, added_at FROM approved_users ORDER BY added_at"
            )
            rows = cursor.fetchall()
        except Exception as e:
            logger.error("Failed to list users: %s", e)
            await ctx.send("❌ Failed to retrieve user list.")
            return

        if not rows:
            embed = discord.Embed(
                title="👥 Approved Users",
                description="No approved users.",
                color=discord.Color.blue(),
            )
            await ctx.send(embed=embed)
            return

        user_lines = []
        for row in rows:
            uid = row["user_id"]
            uname = row["username"] or "Unknown"
            dname = row["display_name"] or "Unknown"
            user_lines.append(
                f"• **{dname}** (@{uname}) — `{uid}`"
            )

        embed = discord.Embed(
            title="👥 Approved Users",
            description="\n".join(user_lines),
            color=discord.Color.blue(),
        )
        embed.set_footer(text=f"Total: {len(rows)} user(s)")
        await ctx.send(embed=embed)

    # ============================================================
    # Access Requests
    # ============================================================

    @commands.command(name="requestaccess")
    async def requestaccess(self, ctx: commands.Context) -> None:
        """Submit an access request to the bot owner.

        Usage: !requestaccess
        """
        user_id = str(ctx.author.id)
        username = str(ctx.author.name)
        display_name = str(ctx.author.display_name)
        guild = ctx.guild.name if ctx.guild else "Unknown"

        try:
            conn = get_connection(self.bot.config.database_path)
            cursor = conn.cursor()

            # Check if already approved
            cursor.execute(
                "SELECT 1 FROM approved_users WHERE user_id = ?",
                (user_id,),
            )
            if cursor.fetchone():
                await ctx.send("✅ You are already approved.")
                return

            # Check if already has a pending request
            cursor.execute(
                "SELECT 1 FROM access_requests WHERE user_id = ? AND status = 'pending'",
                (user_id,),
            )
            if cursor.fetchone():
                await ctx.send("⏳ You already have a pending access request.")
                return

            # Insert new request
            cursor.execute(
                """INSERT INTO access_requests (user_id, username, display_name, guild, status)
                   VALUES (?, ?, ?, ?, 'pending')""",
                (user_id, username, display_name, guild),
            )
            conn.commit()
        except Exception as e:
            logger.error("Failed to create access request for %s: %s", user_id, e)
            await ctx.send("❌ Failed to submit access request.")
            return

        # Notify the owner via DM
        try:
            owner = await self.bot.fetch_user(self.bot.config.owner_id)
            if owner:
                owner_embed = discord.Embed(
                    title="🔔 New Access Request",
                    color=discord.Color.blue(),
                )
                owner_embed.add_field(name="Username", value=username, inline=True)
                owner_embed.add_field(name="Display Name", value=display_name, inline=True)
                owner_embed.add_field(name="User ID", value=f"`{user_id}`", inline=False)
                owner_embed.add_field(name="Guild", value=guild, inline=True)
                owner_embed.set_footer(text="Use !approve or !deny to manage this request")
                await owner.send(embed=owner_embed)
        except Exception as e:
            logger.warning("Failed to notify owner about access request: %s", e)

        await ctx.send("✅ Your access request has been submitted.")

    @commands.command(name="pendingrequests")
    async def pendingrequests(self, ctx: commands.Context) -> None:
        """Show all pending access requests.

        Usage: !pendingrequests
        """
        if not await self._check_owner(ctx):
            return

        try:
            conn = get_connection(self.bot.config.database_path)
            cursor = conn.cursor()
            cursor.execute(
                """SELECT id, user_id, username, display_name, guild, requested_at
                   FROM access_requests WHERE status = 'pending' ORDER BY requested_at"""
            )
            rows = cursor.fetchall()
        except Exception as e:
            logger.error("Failed to list pending requests: %s", e)
            await ctx.send("❌ Failed to retrieve pending requests.")
            return

        if not rows:
            embed = discord.Embed(
                title="📋 Pending Access Requests",
                description="No pending requests.",
                color=discord.Color.blue(),
            )
            await ctx.send(embed=embed)
            return

        request_lines = []
        for row in rows:
            rid = row["id"]
            uid = row["user_id"]
            uname = row["username"] or "Unknown"
            dname = row["display_name"] or "Unknown"
            guild = row["guild"] or "Unknown"
            request_lines.append(
                f"`#{rid}` **{dname}** (@{uname}) — `{uid}` — {guild}"
            )

        embed = discord.Embed(
            title="📋 Pending Access Requests",
            description="\n".join(request_lines),
            color=discord.Color.blue(),
        )
        embed.set_footer(text=f"Total: {len(rows)} pending request(s)")
        await ctx.send(embed=embed)

    @commands.command(name="approve")
    async def approve(self, ctx: commands.Context, *, user_input: str) -> None:
        """Approve a pending access request and add the user to the whitelist.

        Usage: !approve <user_id_or_mention>
        """
        if not await self._check_owner(ctx):
            return

        user_id = _resolve_user_id(user_input)
        if not user_id:
            await ctx.send("❌ Invalid user ID or mention.")
            return

        try:
            conn = get_connection(self.bot.config.database_path)
            cursor = conn.cursor()

            # Get the request info
            cursor.execute(
                "SELECT username, display_name FROM access_requests WHERE user_id = ? AND status = 'pending'",
                (user_id,),
            )
            row = cursor.fetchone()
            username = row["username"] if row else "Unknown"
            display_name = row["display_name"] if row else "Unknown"

            # Update request status
            cursor.execute(
                "UPDATE access_requests SET status = 'approved' WHERE user_id = ? AND status = 'pending'",
                (user_id,),
            )

            # Add to approved users
            cursor.execute(
                """INSERT OR IGNORE INTO approved_users (user_id, username, display_name, added_by)
                   VALUES (?, ?, ?, ?)""",
                (user_id, username, display_name, str(ctx.author.id)),
            )
            conn.commit()
        except Exception as e:
            logger.error("Failed to approve user %s: %s", user_id, e)
            await ctx.send("❌ Failed to approve user.")
            return

        await self._log_audit("approve", user_id, username, str(ctx.author.id))
        await ctx.send("✅ User approved successfully.")

    @commands.command(name="deny")
    async def deny(self, ctx: commands.Context, *, user_input: str) -> None:
        """Deny a pending access request.

        Usage: !deny <user_id_or_mention>
        """
        if not await self._check_owner(ctx):
            return

        user_id = _resolve_user_id(user_input)
        if not user_id:
            await ctx.send("❌ Invalid user ID or mention.")
            return

        try:
            conn = get_connection(self.bot.config.database_path)
            cursor = conn.cursor()

            # Get the request info
            cursor.execute(
                "SELECT username, display_name FROM access_requests WHERE user_id = ? AND status = 'pending'",
                (user_id,),
            )
            row = cursor.fetchone()
            username = row["username"] if row else "Unknown"

            # Update request status
            cursor.execute(
                "UPDATE access_requests SET status = 'denied' WHERE user_id = ? AND status = 'pending'",
                (user_id,),
            )
            conn.commit()
        except Exception as e:
            logger.error("Failed to deny request for %s: %s", user_id, e)
            await ctx.send("❌ Failed to deny request.")
            return

        await self._log_audit("deny", user_id, username, str(ctx.author.id))
        await ctx.send("✅ Request denied.")

    # ============================================================
    # Blacklist Management
    # ============================================================

    @commands.command(name="blacklist")
    async def blacklist(self, ctx: commands.Context, *, user_input: str) -> None:
        """Blacklist a user, overriding whitelist.

        Usage: !blacklist <user_id_or_mention>
        """
        if not await self._check_owner(ctx):
            return

        user_id = _resolve_user_id(user_input)
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
            cursor = conn.cursor()
            cursor.execute(
                """INSERT OR IGNORE INTO blacklisted_users (user_id, username, display_name, added_by)
                   VALUES (?, ?, ?, ?)""",
                (user_id, username, display_name, str(ctx.author.id)),
            )
            conn.commit()
        except Exception as e:
            logger.error("Failed to blacklist user %s: %s", user_id, e)
            await ctx.send("❌ Failed to blacklist user.")
            return

        await self._log_audit("blacklist", user_id, username, str(ctx.author.id))
        await ctx.send("✅ User blacklisted.")

    @commands.command(name="unblacklist")
    async def unblacklist(self, ctx: commands.Context, *, user_input: str) -> None:
        """Remove a user from the blacklist.

        Usage: !unblacklist <user_id_or_mention>
        """
        if not await self._check_owner(ctx):
            return

        user_id = _resolve_user_id(user_input)
        if not user_id:
            await ctx.send("❌ Invalid user ID or mention.")
            return

        try:
            conn = get_connection(self.bot.config.database_path)
            cursor = conn.cursor()

            cursor.execute(
                "SELECT username FROM blacklisted_users WHERE user_id = ?",
                (user_id,),
            )
            row = cursor.fetchone()
            target_username = row["username"] if row else "Unknown"

            cursor.execute(
                "DELETE FROM blacklisted_users WHERE user_id = ?",
                (user_id,),
            )
            conn.commit()
        except Exception as e:
            logger.error("Failed to unblacklist user %s: %s", user_id, e)
            await ctx.send("❌ Failed to unblacklist user.")
            return

        await self._log_audit("unblacklist", user_id, target_username, str(ctx.author.id))
        await ctx.send("✅ User unblacklisted.")

    # ============================================================
    # User Info
    # ============================================================

    @commands.command(name="whoami")
    async def whoami(self, ctx: commands.Context) -> None:
        """Display your user information and access status.

        Usage: !whoami
        """
        user_id = str(ctx.author.id)
        username = str(ctx.author.name)
        display_name = str(ctx.author.display_name)
        guild = ctx.guild.name if ctx.guild else "N/A"
        channel = ctx.channel.name if ctx.channel else "N/A"

        is_authorized = await self._is_authorized(ctx)
        is_blacklisted = False

        try:
            conn = get_connection(self.bot.config.database_path)
            cursor = conn.cursor()
            cursor.execute(
                "SELECT 1 FROM blacklisted_users WHERE user_id = ?",
                (user_id,),
            )
            is_blacklisted = cursor.fetchone() is not None
        except Exception:
            pass

        embed = discord.Embed(
            title="👤 User Info",
            color=discord.Color.green() if is_authorized else discord.Color.red(),
        )
        embed.add_field(name="Username", value=f"@{username}", inline=True)
        embed.add_field(name="Display Name", value=display_name, inline=True)
        embed.add_field(name="User ID", value=f"`{user_id}`", inline=False)
        embed.add_field(name="Guild", value=guild, inline=True)
        embed.add_field(name="Channel", value=channel, inline=True)
        embed.add_field(
            name="Access Status",
            value="✅ Authorized" if is_authorized else "❌ Not Authorized",
            inline=False,
        )
        embed.add_field(
            name="Blacklist Status",
            value="🚫 Blacklisted" if is_blacklisted else "✅ Not Blacklisted",
            inline=False,
        )

        await ctx.send(embed=embed)

    # ============================================================
    # Status
    # ============================================================

    @commands.command(name="status")
    async def status(self, ctx: commands.Context) -> None:
        """Display bot status information.

        Usage: !status
        """
        config = self.bot.config

        # Lavalink status
        lavalink_status = "Disconnected"
        try:
            import wavelink
            node = wavelink.Pool.get_node()
            if node:
                lavalink_status = f"Connected ({round(node.latency)}ms)"
        except Exception:
            pass

        # Queue length and current track
        guild_id = config.guild_id
        queue_length = self.bot.queue_manager.get_length(guild_id)
        current_track = "None"
        player = discord.utils.get(self.bot.voice_clients, guild__id=guild_id)
        if player and player.playing and player.last_track:
            current_track = player.last_track.title

        # Uptime
        uptime = "N/A"
        if hasattr(self.bot, "get_uptime"):
            uptime = await self.bot.get_uptime()

        embed = discord.Embed(
            title="🤖 Bot Status",
            color=discord.Color.green(),
        )
        embed.add_field(name="Guild ID", value=f"`{config.guild_id}`", inline=True)
        embed.add_field(name="Music Channel ID", value=f"`{config.music_channel_id}`", inline=True)
        embed.add_field(name="Lavalink Status", value=lavalink_status, inline=False)
        embed.add_field(name="Queue Length", value=str(queue_length), inline=True)
        embed.add_field(name="Current Track", value=current_track or "None", inline=True)
        embed.add_field(name="Bot Uptime", value=uptime, inline=False)

        await ctx.send(embed=embed)

    # ============================================================
    # 24/7 Mode
    # ============================================================

    @commands.command(name="247")
    async def toggle_247(self, ctx: commands.Context, *, state: str) -> None:
        """Toggle 24/7 mode on or off (owner only).

        Usage: !247 on or !247 off
        """
        if not await self._check_owner(ctx):
            return

        state_lower = state.strip().lower()
        if state_lower not in ("on", "off"):
            await ctx.send("❌ Usage: `!247 on` or `!247 off`")
            return

        value = "true" if state_lower == "on" else "false"

        try:
            conn = get_connection(self.bot.config.database_path)
            cursor = conn.cursor()
            cursor.execute(
                "INSERT OR REPLACE INTO bot_settings (key, value) VALUES ('247_enabled', ?)",
                (value,),
            )
            conn.commit()
        except Exception as e:
            logger.error("Failed to update 24/7 setting: %s", e)
            await ctx.send("❌ Failed to update 24/7 mode.")
            return

        status_text = "enabled" if state_lower == "on" else "disabled"
        await ctx.send(f"✅ 24/7 mode {status_text}.")


async def setup(bot: commands.Bot) -> None:
    """Add the admin commands cog to the bot."""
    await bot.add_cog(AdminCommands(bot))
    logger.info("Admin commands cog loaded")