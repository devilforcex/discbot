"""E2E tests for chat workflow."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from bot.cogs.chat.commands import ChatCog
from bot.core.services.ai_service import AIService

@pytest.mark.asyncio
async def test_e2e_chat_flow():
    """Test full e2e chat flow."""
    mock_config = MagicMock()
    mock_config.ai_enabled = True
    
    with patch("bot.cogs.chat.commands.get_config", return_value=mock_config):
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
        
        await cog.chat_command(ctx, question="hi")
        
        assert ai_service.get_history(123, 456)
        ctx.send.assert_called_with("Hello!")
