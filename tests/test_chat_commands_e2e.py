"""E2E tests for chat workflow."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from bot.cogs.chat.commands import ChatCog
from bot.core.services.ai_service import AIService

@pytest.mark.asyncio
async def test_e2e_chat_flow():
    """Test full e2e chat flow."""
    mock_config = MagicMock(spec=["ai_enabled", "ai_system_prompt", "ai_max_history", "ai_default_model", "ai_temperature"])
    mock_config.ai_enabled = True
    mock_config.ai_system_prompt = "Test"
    mock_config.ai_max_history = 10
    mock_config.ai_default_model = "gpt-4o-mini"
    mock_config.ai_temperature = 0.7
    
    with (
        patch("bot.cogs.chat.commands.get_config", return_value=mock_config),
        patch("bot.cogs.chat.base.get_config", return_value=mock_config),
    ):
        ai_service = AIService(mock_config)
        ai_service._build_config = MagicMock()
        
        # Mock the client directly to avoid network calls
        ai_service._clients = [AsyncMock()]
        ai_service._clients[0].chat.completions.create = AsyncMock(
            return_value=MagicMock(choices=[MagicMock(message=MagicMock(content="Hello!"))])
        )
        
        mock_bot = MagicMock()
        cog = ChatCog(mock_bot)
        cog.config = mock_config
        cog.ai_service = ai_service
        
        ctx = AsyncMock()
        ctx.guild.id = 123
        ctx.author.id = 456
        
        await cog.chat_command.callback(cog, ctx, question="hi")
        
        assert ai_service.get_history(123, 456)
        ctx.send.assert_called_with("Hello!")
