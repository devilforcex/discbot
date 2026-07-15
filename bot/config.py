"""
Configuration module for the Discord Music Bot.
Loads and validates environment variables using pydantic-settings.
"""

from pathlib import Path
from typing import Optional

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings


class Config(BaseSettings):
    """Application configuration loaded from environment variables."""

    # Discord
    discord_bot_token: str = Field(
        default="",
        description="Discord bot token from Discord Developer Portal",
    )

    # Guild/Channel Restrictions
    guild_id: int = Field(
        default=1074037877899542538,
        description="Discord guild ID the bot is restricted to",
    )
    music_channel_id: int = Field(
        default=1097945134630445227,
        description="Channel ID where music commands are allowed",
    )
    owner_id: int = Field(
        default=954887574248374322,
        description="Bot owner/super-admin user ID",
    )

    # Lavalink
    lavalink_host: str = Field(
        default="127.0.0.1",
        description="Lavalink server hostname",
    )
    lavalink_port: int = Field(
        default=12333,
        description="Lavalink server port",
        ge=1,
        le=65535,
    )
    lavalink_password: str = Field(
        default="youshallnotpass",
        description="Lavalink server password",
    )
    lavalink_secure: bool = Field(
        default=False,
        description="Use HTTPS for the Lavalink node URI",
    )
    youtube_cookies_enabled: bool = Field(
        default=True,
        description="Enable YouTube cookies for age-restricted/region-locked video playback",
    )

    # Spotify (optional)
    spotify_client_id: Optional[str] = Field(
        default=None,
        description="Spotify API client ID (optional, for Spotify URL support)",
    )
    spotify_client_secret: Optional[str] = Field(
        default=None,
        description="Spotify API client secret (optional)",
    )

    # Database
    database_path: str = Field(
        default="data/musicbot.db",
        description="Path to SQLite database file",
    )

    # Logging
    log_level: str = Field(
        default="INFO",
        description="Logging level: DEBUG, INFO, WARNING, ERROR, CRITICAL",
    )

    # Dashboard
    dashboard_enabled: bool = Field(
        default=False,
        description="Enable the web dashboard",
    )
    dashboard_host: str = Field(
        default="127.0.0.1",
        description="Dashboard server host",
    )
    dashboard_port: int = Field(
        default=18080,
        description="Dashboard server port",
        ge=1,
        le=65535,
    )
    dashboard_secret_key: str = Field(
        default="change_me_to_a_random_secret_key",
        description="Secret key for dashboard session/auth",
    )

    # Branding & Links — for help menu & website (Steel)
    support_server_url: Optional[str] = Field(
        default=None,
        description="Discord support server invite URL",
    )
    discord_invite_url: Optional[str] = Field(
        default=None,
        description="Alias for support server invite",
    )
    bot_invite_url: Optional[str] = Field(
        default=None,
        description="Bot invite URL (OAuth2)",
    )
    website_url: Optional[str] = Field(
        default="https://github.com/devilforcex/discbot",
        description="Website / Vote URL for help menu buttons",
    )
    made_by_text: str = Field(
        default="Made with ❤️ by Steel",
        description="Footer branding text",
    )

    @model_validator(mode="after")
    def validate_token(self) -> "Config":
        """Ensure Discord bot token is provided."""
        if not self.discord_bot_token or self.discord_bot_token == "your_bot_token_here":
            raise ValueError(
                "DISCORD_BOT_TOKEN is not set. "
                "Copy .env.example to .env and set your bot token."
            )
        return self

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
        "extra": "ignore",
    }


_config_instance: Optional[Config] = None


def load_config() -> Config:
    """Load configuration from environment variables and .env file.

    Returns:
        Config: Validated configuration instance.

    Raises:
        ValueError: If required configuration is missing or invalid.
    """
    global _config_instance

    # Try loading from .env file
    env_path = Path(".env")
    if env_path.exists():
        from dotenv import load_dotenv
        load_dotenv(env_path)

    _config_instance = Config()
    return _config_instance


def get_config() -> Config:
    """Get the cached configuration instance.

    Returns:
        Config: The loaded configuration instance.

    Raises:
        RuntimeError: If configuration has not been loaded yet.
    """
    if _config_instance is None:
        raise RuntimeError(
            "Configuration not loaded. Call load_config() first."
        )
    return _config_instance