"""
Custom Bot subclass for the Discord Music Bot.
Manages subsystem lifecycle, cog loading, and global state.
"""

import asyncio
import contextlib
import logging
import os
from datetime import UTC, datetime
from typing import TYPE_CHECKING

import discord
import wavelink
from discord.ext import commands

from bot.config import Config, load_config
from bot.music.lavalink_client import LavalinkClient
from bot.music.queue_manager import QueueManager

if TYPE_CHECKING:
    from bot.database.repository import Repository
    from bot.music.player_controller import PlayerController
    from bot.music.player_message import PlayerMessageManager

logger = logging.getLogger(__name__)


class Bot(commands.Bot):
    """Custom Bot with extended functionality for music playback.

    Manages configuration, Lavalink client, queue manager, database,
    auto-reconnect, 24/7 mode, and optional dashboard as first-class attributes.
    """

    queue_manager: QueueManager
    lavalink: LavalinkClient
    player_controller: "PlayerController"
    player_messages: "PlayerMessageManager"
    db: "Repository | None"

    def __init__(self, config: Config | None = None):
        # Load configuration if not provided
        self._config = config or load_config()

        # Bot intents
        intents = discord.Intents.default()
        intents.message_content = True  # Required for prefix commands
        intents.voice_states = True  # Required for voice channel tracking
        intents.guilds = True  # Required for guild tracking

        super().__init__(
            command_prefix="!",
            intents=intents,
            help_command=None,  # Disable default help to use custom !help command
        )

        # Initialize subsystems
        # Remove default help command to allow custom !help
        self._io_loop: asyncio.AbstractEventLoop | None = None
        self.queue_manager = QueueManager()
        self.lavalink = LavalinkClient(self)
        self._dashboard = None

        # Interactive player (controller + persistent NP message)
        from bot.music.player_controller import PlayerController
        from bot.music.player_message import PlayerMessageManager

        self.player_controller = PlayerController(self)
        self.player_messages = PlayerMessageManager(self)

        # Uptime tracking
        self._start_time: datetime | None = None

        # Lavalink auto-reconnect
        self._lavalink_reconnect_attempt: int = 0
        self._lavalink_reconnect_task: asyncio.Task | None = None

    @property
    def config(self) -> Config:
        """Get the bot configuration."""
        return self._config

    async def setup_hook(self) -> None:
        """Initialize subsystems and load cogs on startup."""
        logger.info("Starting bot setup...")

        # Setup Lavalink.  A missing Lavalink server should not prevent the
        # Discord bot from coming online; commands can fail gracefully while
        # the background reconnect task keeps trying.
        try:
            await self.lavalink.setup(self._config)
            logger.info("Lavalink client initialized")
        except Exception as e:
            logger.warning(
                "Initial Lavalink connection failed; bot will retry in the background: %s",
                e,
            )
            self._schedule_lavalink_reconnect()

        # Load cogs — refactored into focused modules
        cogs_to_load = [
            "bot.core.errors",
            "bot.music.lavalink_client",
            # Admin (split from 695-line monolith)
            "bot.cogs.admin.whitelist",
            "bot.cogs.admin.blacklist",
            "bot.cogs.admin.requests",
            "bot.cogs.admin.misc",
            # Music (split from 827-line monolith)
            "bot.cogs.music.playback",
            "bot.cogs.music.queue_cmds",
            "bot.cogs.music.filters",
            "bot.cogs.music.library",
            "bot.cogs.music.utility",
            # AI Chat
            "bot.cogs.chat.commands",
            "bot.cogs.events",
        ]

        for cog_path in cogs_to_load:
            try:
                await self.load_extension(cog_path)
                logger.info("Loaded cog: %s", cog_path)
            except Exception as e:
                logger.error("Failed to load cog %s: %s", cog_path, e)

        # Initialize database
        await self._init_database()

        # Setup dashboard if enabled, or when running as a web service (e.g. a PaaS
        # that injects $PORT and healthchecks the service). The dashboard must always
        # run so the /api/health endpoint is reachable — otherwise deployments fail.
        dashboard_on = self._config.dashboard_enabled or bool(os.environ.get("PORT"))
        if dashboard_on:
            await self._setup_dashboard()

        # Initialize AI service
        try:
            from bot.core.services.ai_service import init_ai_service

            init_ai_service(self._config)
            logger.info("AI service initialized: %s", "enabled" if self._config.ai_enabled else "disabled")
        except Exception as e:
            logger.error("AI service initialization failed: %s", e)

        logger.info("Bot setup complete")

    async def _init_database(self) -> None:
        """Initialize database via the unified repository (PostgreSQL or SQLite fallback)."""
        try:
            from bot.database.repository import create_repository

            self.db = await create_repository(
                db_path=self._config.database_path,
                database_url=self._config.database_url,
            )
            backend = "PostgreSQL" if self.db.is_postgres else "SQLite"
            logger.info("Database initialized — backend: %s", backend)
        except Exception as e:
            logger.error("Database initialization failed: %s", e)
            self.db = None

    async def _setup_dashboard(self) -> None:
        """Setup the optional web dashboard."""
        try:
            from bot.dashboard.dashboard import DashboardServer

            self._dashboard = DashboardServer(self)

            # Start dashboard in background
            asyncio.create_task(self._dashboard.start())
            logger.info(
                "Dashboard starting at http://%s:%s",
                self._config.dashboard_host,
                self._config.dashboard_port,
            )
        except ImportError as e:
            logger.warning("Dashboard dependencies not installed: %s", e)
        except Exception as e:
            logger.error("Dashboard setup failed: %s", e)

    async def on_ready(self) -> None:
        """Handle bot ready event."""
        self._start_time = datetime.now(UTC)

        logger.info(
            "Bot is ready! Logged in as %s (ID: %s)",
            self.user,
            self.user.id if self.user else "unknown",
        )
        logger.info("Connected to %d guild(s)", len(self.guilds))

        # Set bot presence
        activity = discord.Activity(
            type=discord.ActivityType.listening,
            name="!help · player buttons",
        )
        await self.change_presence(activity=activity)

        # Restore persistent player button views after restart
        try:
            await self.player_messages.restore_views()
        except Exception as e:
            logger.warning("Failed to restore player views: %s", e)

        # Auto-join music channel if 24/7 mode is enabled
        await self._auto_join_music_channel()

    async def on_message(self, message: discord.Message) -> None:
        """Process prefix commands."""
        if message.author.bot:
            return
        await self.process_commands(message)

    async def _auto_join_music_channel(self) -> None:
        """Auto-join the configured music voice channel if 24/7 mode is enabled."""
        try:
            if not hasattr(self, "db") or not self.db:
                return
            row = await self.db.fetchrow("SELECT value FROM bot_settings WHERE key = '247_enabled'")
            if not row or row.get("value") != "true":
                return
        except Exception as e:
            logger.debug("Failed to check 24/7 setting: %s", e)
            return

        # Find the guild and voice channel
        guild = self.get_guild(self._config.guild_id)
        if not guild:
            logger.warning("Cannot auto-join: guild %s not found", self._config.guild_id)
            return

        # Try to join the configured voice channel directly
        voice_channel_id = getattr(self._config, "music_voice_channel_id", None)
        if not voice_channel_id:
            logger.warning("Cannot auto-join: music_voice_channel_id not configured")
            return

        voice_channel = guild.get_channel(voice_channel_id)
        if not voice_channel:
            logger.warning("Cannot auto-join: voice channel %s not found", voice_channel_id)
            return

        if not isinstance(voice_channel, discord.VoiceChannel):
            logger.warning("Configured channel %s is not a voice channel", voice_channel_id)
            return

        try:
            await self.lavalink.get_player(guild.id, voice_channel)
            logger.info("24/7 auto-joined voice channel: %s", voice_channel.name)
        except Exception as e:
            logger.error("24/7 auto-join failed: %s", e)

    def _schedule_lavalink_reconnect(self) -> None:
        """Start a single Lavalink reconnect task if one is not already running."""
        if self._lavalink_reconnect_task and not self._lavalink_reconnect_task.done():
            return
        self._lavalink_reconnect_task = asyncio.create_task(self._auto_reconnect_lavalink())

    async def _auto_reconnect_lavalink(self) -> None:
        """Background task to reconnect to Lavalink with exponential backoff."""
        max_delay = 60  # Maximum delay in seconds
        base_delay = 1  # Starting delay in seconds

        while True:
            try:
                # Check if already connected
                node = wavelink.Pool.get_node()
                if node and node.is_connected:
                    self._lavalink_reconnect_attempt = 0
                    return

                delay = min(base_delay * (2**self._lavalink_reconnect_attempt), max_delay)
                self._lavalink_reconnect_attempt += 1

                logger.warning(
                    "Attempting Lavalink reconnection in %ds (attempt %d)...",
                    delay,
                    self._lavalink_reconnect_attempt,
                )

                await asyncio.sleep(delay)

                # Try to reconnect
                await self.lavalink.setup(self._config)
                logger.info(
                    "Lavalink reconnected successfully after %d attempts",
                    self._lavalink_reconnect_attempt,
                )
                self._lavalink_reconnect_attempt = 0
                return

            except asyncio.CancelledError:
                return
            except Exception as e:
                logger.error("Lavalink reconnect attempt failed: %s", e)

    async def get_uptime(self) -> str:
        """Get the bot's uptime as a formatted string."""
        if self._start_time is None:
            return "N/A"
        delta = datetime.now(UTC) - self._start_time
        days = delta.days
        hours, remainder = divmod(delta.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        parts = []
        if days > 0:
            parts.append(f"{days}d")
        if hours > 0:
            parts.append(f"{hours}h")
        if minutes > 0:
            parts.append(f"{minutes}m")
        parts.append(f"{seconds}s")
        return " ".join(parts)

    async def close(self) -> None:
        """Clean shutdown of all subsystems."""
        logger.info("Shutting down bot...")

        # Stop reconnect loop first so shutdown doesn't spawn a new node task.
        if self._lavalink_reconnect_task and not self._lavalink_reconnect_task.done():
            self._lavalink_reconnect_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._lavalink_reconnect_task

        # Stop dashboard if running
        if self._dashboard:
            try:
                await self._dashboard.stop()
            except Exception as e:
                logger.error("Dashboard shutdown error: %s", e)

        # Disconnect Lavalink
        try:
            await self.lavalink.close()
        except Exception as e:
            logger.error("Lavalink shutdown error: %s", e)

        # Close database (repository handles both backends)
        if hasattr(self, "db") and self.db:
            try:
                await self.db.shutdown()
                logger.info("Database connection closed")
            except Exception as e:
                logger.error("Database shutdown error: %s", e)

        await super().close()
        logger.info("Bot shutdown complete")


def run_bot() -> None:
    """Entry point to create and run the bot."""
    import asyncio

    # Load configuration
    config = load_config()

    # Setup logging
    from bot.core.logging_setup import setup_logging

    setup_logging(config.log_level)

    # Create and run bot
    bot = Bot(config)

    try:
        bot.run(config.discord_bot_token)
    except KeyboardInterrupt:
        asyncio.run(bot.close())
    except Exception as e:
        logger.critical("Fatal error: %s", e)
        raise
