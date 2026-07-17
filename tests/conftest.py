"""Pytest configuration and fixtures for DiscBot tests."""

from __future__ import annotations

import os
import sys
from unittest.mock import MagicMock

import pytest

# Ensure project root is on sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def pytest_configure(config):
    """Register custom markers."""
    for marker, desc in [
        ("unit", "Mark test as a unit test"),
        ("integration", "Mark test as an integration test"),
        ("ai", "Mark test as an AI service test"),
        ("discord", "Mark test as a Discord-related test"),
        ("slow", "Mark test as a slow test requiring external services"),
    ]:
        config.addinivalue_line("markers", f"{marker}: {desc}")


def pytest_collection_modifyitems(items):
    """Auto-apply markers based on file path."""
    for item in items:
        path = str(item.fspath).lower()
        if "integration" in path:
            item.add_marker(pytest.mark.integration)
        else:
            item.add_marker(pytest.mark.unit)
        if "ai" in path:
            item.add_marker(pytest.mark.ai)
        if "discord" in path:
            item.add_marker(pytest.mark.discord)


@pytest.fixture
def mock_config():
    """Mock Config for testing without loading .env."""
    config = MagicMock()
    config.discord_bot_token = "test_token"
    config.guild_id = 0
    config.music_channel_id = 0
    config.music_voice_channel_id = 0
    config.owner_id = 0
    config.lavalink_host = "127.0.0.1"
    config.lavalink_port = 12333
    config.lavalink_password = "youshallnotpass"
    config.lavalink_secure = False
    config.youtube_cookies_enabled = True
    config.spotify_client_id = None
    config.spotify_client_secret = None
    config.database_path = ":memory:"
    config.database_url = None
    config.log_level = "INFO"
    config.dashboard_enabled = False
    config.dashboard_host = "0.0.0.0"
    config.dashboard_port = 18080
    config.dashboard_secret_key = "test_secret_key_min_32_chars_padding"
    config.support_server_url = None
    config.discord_invite_url = None
    config.bot_invite_url = None
    config.website_url = None
    config.made_by_text = "Test"
    # AI config
    config.ai_enabled = True
    config.ai_provider = "omniroute"
    config.omniroute_base_url = "http://localhost:20128/v1"
    config.omniroute_api_key = "test-key"
    config.omniroute_api_keys_fallback = ""
    config.openai_api_key = None
    config.ai_default_model = "gpt-4o-mini"
    config.ai_system_prompt = "Test assistant"
    config.ai_max_history = 10
    config.ai_temperature = 0.7
    return config
