"""Integration tests for chat commands."""

from unittest.mock import AsyncMock, MagicMock, patch
import pytest
import discord
from bot.cogs.chat.commands import ChatCog

@pytest.fixture
def chat_cog(mock_config):
    with (
        patch("bot.cogs.chat.commands.get_config", return_value=mock_config),
        patch("bot.cogs.chat.base.get_config", return_value=mock_config),
    ):
        mock_bot = MagicMock()
        return ChatCog(mock_bot)

@pytest.mark.asyncio
async def test_chat_command_enabled(chat_cog, mock_config):
    """Test chat command when enabled."""
    chat_cog.config.ai_enabled = True
    chat_cog.ai_service = AsyncMock()
    chat_cog.ai_service.chat.return_value = "AI response"
    
    ctx = AsyncMock()
    ctx.guild.id = 123
    ctx.author.id = 456
    
    with patch("bot.cogs.chat.base.get_config", return_value=mock_config):
        await chat_cog.chat_command.callback(chat_cog, ctx, question="hello")
    
    chat_cog.ai_service.chat.assert_called_once()
    ctx.send.assert_called_with("AI response")

@pytest.mark.asyncio
async def test_chat_command_disabled(chat_cog, mock_config):
    """Test chat command when disabled."""
    chat_cog.config.ai_enabled = False
    chat_cog.ai_service = AsyncMock()
    
    ctx = AsyncMock()
    with (
        patch("bot.cogs.chat.commands.check_ai_enabled", return_value=False),
        patch("bot.cogs.chat.base.get_config", return_value=mock_config),
    ):
        await chat_cog.chat_command.callback(chat_cog, ctx, question="hello")
        
    chat_cog.ai_service.chat.assert_not_called()
