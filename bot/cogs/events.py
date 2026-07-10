"""
Event handler cog for the Discord Music Bot.
Handles guild join/leave, voice state updates, and bot lifecycle events.
"""

import logging
import discord
from discord.ext import commands

logger = logging.getLogger(__name__)


class EventCog(commands.Cog):
    """Handles Discord events for guild management and voice state tracking."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    def _is_247_enabled(self) -> bool:
        """Return whether 24/7 mode is enabled in persistent settings."""
        try:
            from bot.database.database import get_connection

            conn = get_connection(self.bot.config.database_path)
            cursor = conn.cursor()
            cursor.execute("SELECT value FROM bot_settings WHERE key = '247_enabled'")
            row = cursor.fetchone()
            return bool(row and row["value"] == "true")
        except Exception as e:
            logger.debug("Failed to read 24/7 setting: %s", e)
            return False

    @commands.Cog.listener()
    async def on_guild_join(self, guild: discord.Guild) -> None:
        """Initialize guild settings when the bot joins a new guild.

        Args:
            guild: The guild the bot joined.
        """
        logger.info("Bot joined guild: %s (ID: %s)", guild.name, guild.id)

        # Initialize guild settings
        try:
            from bot.database import guild_settings as gs
            gs.get(str(guild.id), self.bot.config.database_path)
            logger.info("Initialized settings for guild: %s", guild.name)
        except Exception as e:
            logger.error("Failed to initialize settings for guild %s: %s", guild.name, e)

    @commands.Cog.listener()
    async def on_guild_remove(self, guild: discord.Guild) -> None:
        """Clean up guild data when the bot leaves a guild.

        Args:
            guild: The guild the bot left.
        """
        logger.info("Bot removed from guild: %s (ID: %s)", guild.name, guild.id)

        # Clean up queue and player
        self.bot.queue_manager.cleanup(guild.id)

        # Remove guild settings
        try:
            from bot.database import guild_settings as gs
            gs.remove(str(guild.id), self.bot.config.database_path)
            logger.info("Removed settings for guild: %s", guild.name)
        except Exception as e:
            logger.error("Failed to remove settings for guild %s: %s", guild.name, e)

    @commands.Cog.listener()
    async def on_voice_state_update(
        self,
        member: discord.Member,
        before: discord.VoiceState,
        after: discord.VoiceState,
    ) -> None:
        """Handle voice state changes.

        Features:
        - Auto-disconnect when bot is alone in voice channel
        - Track member voice channel changes

        Args:
            member: The member whose voice state changed.
            before: Previous voice state.
            after: New voice state.
        """
        # Ignore bot's own voice state updates (handled by disconnect command)
        if member.bot:
            return

        # Check if the bot is connected to a voice channel in this guild
        voice_client = discord.utils.get(
            self.bot.voice_clients,
            guild__id=member.guild.id,
        )

        if not voice_client or not voice_client.channel:
            return

        # Auto-disconnect if the bot is alone in the voice channel.
        # 24/7 mode intentionally keeps the player connected while idle.
        if self._is_247_enabled():
            return

        voice_channel = voice_client.channel
        if len(voice_channel.members) <= 1:  # Only the bot
            logger.info(
                "Bot is alone in voice channel %s (guild: %s). Disconnecting...",
                voice_channel.name,
                member.guild.name,
            )

            # Delay disconnect to prevent quick reconnects
            import asyncio
            await asyncio.sleep(30)

            # Re-check if still alone and 24/7 was not enabled while waiting.
            if voice_channel and len(voice_channel.members) <= 1 and not self._is_247_enabled():
                await voice_client.disconnect()
                self.bot.queue_manager.cleanup(member.guild.id)
                logger.info("Auto-disconnected from guild %s (alone)", member.guild.name)

    @commands.Cog.listener()
    async def on_resume(self) -> None:
        """Handle bot resume after disconnection."""
        logger.info("Bot resumed connection to Discord")


async def setup(bot: commands.Bot) -> None:
    """Add the events cog to the bot."""
    await bot.add_cog(EventCog(bot))
    logger.info("Events cog loaded")