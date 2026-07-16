"""
Custom error handling for the Discord Music Bot.
Provides error hierarchy, error embeds, and a global error handler cog.
"""

import logging

import discord
from discord.ext import commands

logger = logging.getLogger(__name__)


class MusicBotError(Exception):
    """Base exception for all music bot errors."""

    def __init__(self, message: str, user_message: str | None = None):
        self.message = message
        self.user_message = user_message or message
        super().__init__(self.message)


class NotInVoiceChannel(MusicBotError):
    """User is not connected to a voice channel."""

    def __init__(self):
        super().__init__(
            message="User not in voice channel",
            user_message="You must be in a voice channel to use this command.",
        )


class DifferentVoiceChannel(MusicBotError):
    """User is in a different voice channel than the bot."""

    def __init__(self):
        super().__init__(
            message="User in different voice channel",
            user_message="You must be in the same voice channel as the bot.",
        )


class NoPlayer(MusicBotError):
    """No active player in the guild."""

    def __init__(self):
        super().__init__(
            message="No active player in guild",
            user_message="There is no active music session. Use `!play` to start one.",
        )


class NothingPlaying(MusicBotError):
    """No track is currently playing."""

    def __init__(self):
        super().__init__(
            message="Nothing currently playing",
            user_message="Nothing is currently playing.",
        )


class QueueEmpty(MusicBotError):
    """The queue is empty."""

    def __init__(self):
        super().__init__(
            message="Queue is empty",
            user_message="The queue is empty.",
        )


class TrackNotFound(MusicBotError):
    """No tracks found for the given query."""

    def __init__(self, query: str = ""):
        super().__init__(
            message=f"Track not found: {query}",
            user_message=f"No results found for '{query}'. Please try a different search term or URL.",
        )


class LavalinkNotConnected(MusicBotError):
    """Lavalink node is not connected."""

    def __init__(self):
        super().__init__(
            message="Lavalink not connected",
            user_message="The music system is not connected. Please try again later.",
        )


class PlaylistError(MusicBotError):
    """Base class for playlist-related errors."""

    pass


class PlaylistNotFound(PlaylistError):
    """Playlist does not exist."""

    def __init__(self, playlist_id: str = ""):
        super().__init__(
            message=f"Playlist not found: {playlist_id}",
            user_message="That playlist does not exist.",
        )


class PlaylistMaxTracks(PlaylistError):
    """Playlist has reached maximum track limit."""

    def __init__(self, limit: int = 200):
        super().__init__(
            message=f"Playlist track limit: {limit}",
            user_message=f"Playlists can have a maximum of {limit} tracks.",
        )


class FavoriteNotFound(MusicBotError):
    """Favorite track not found."""

    def __init__(self):
        super().__init__(
            message="Favorite not found",
            user_message="That track is not in your favorites.",
        )


def build_error_embed(
    title: str = "Error",
    description: str = "An unexpected error occurred.",
) -> discord.Embed:
    """Build a standardized error embed.

    Args:
        title: Short error title.
        description: Detailed error description.

    Returns:
        A styled discord.Embed with red color.
    """
    embed = discord.Embed(
        title=f"❌ {title}",
        description=description,
        color=discord.Color.red(),
    )
    return embed


class ErrorHandler(commands.Cog):
    """Global error handler cog for catching and formatting command errors."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_command_error(self, ctx: commands.Context, error: Exception) -> None:
        """Handle legacy prefix command errors (fallback)."""
        logger.error("Command error in %s: %s", ctx.command, error)
        embed = build_error_embed(description=str(error))
        await ctx.send(embed=embed, delete_after=10)


async def setup(bot: commands.Bot) -> None:
    """Add the error handler cog to the bot."""
    await bot.add_cog(ErrorHandler(bot))
    logger.info("Error handler cog loaded")
