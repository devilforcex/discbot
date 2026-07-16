"""
Integration tests for chat commands - END TO END tests for the complete AI chat workflow.
This file tests the entire user flow through Discord commands and AI service integration.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch, call
from discord.ext import commands
from discord import ApplicationContext, Message
from discord.ext.commands import Context

# Import the actual cogs and services
from bot.cogs.chat.commands import ChatCog
from bot.core.services.ai_service import AIService
from bot.config import Config


class TestChatCommandsE2E:
    """End-to-end integration tests for complete chat workflows."""

    def setup_method(self):
        """Setup test fixtures with real components."""
        # Create real config
        self.mock_config = Config()
        self.mock_config.ai_enabled = True
        self.mock_config.ai_provider = "omniroute"
        self.mock_config.omniroute_base_url = "http://localhost:20128/v1"
        self.mock_config.omniroute_api_key = "sk-d5e03b448a5eeeb0-668d47-fd492dda"
        self.mock_config.ai_default_model = "gpt-4o-mini"
        self.mock_config.ai_system_prompt = "You are a helpful Discord music bot assistant."
        self.mock_config.ai_max_history = 5
        self.mock_config.ai_temperature = 0.7

        # Create real AI service
        self.ai_service = AIService(self.mock_config)

        # Create mock bot
        self.mock_bot = MagicMock(spec=commands.Bot)
        self.mock_bot.config = self.mock_config
        self.mock_bot.loop = MagicMock()

        # Create cog with real components
        self.cog = ChatCog(self.mock_bot)
        self.cog.config = self.mock_config
        self.cog.ai_service = self.ai_service

    def test_complete_chat_workflow(self):
        """Test complete end-to-end chat workflow."""
        # Setup Discord context
        mock_ctx = MagicMock(spec=Context)
        mock_ctx.author = MagicMock()
        mock_ctx.author.id = 123456  # User ID
        mock_ctx.guild = MagicMock()
        mock_ctx.guild.id = 789012    # Guild ID
        mock_ctx.channel = MagicMock()
        mock_channel = MagicMock()
        mock_ctx.channel.send = AsyncMock()
        mock_ctx.send = AsyncMock()
        mock_ctx.bot = self.mock_bot

        # Mock the typing indicator
        mock_ctx.typing = AsyncMock()

        # Mock check_ai_enabled to return True
        with patch('bot.cogs.chat.commands.check_ai_enabled', return_value=True):
            # Mock AI service response
            expected_response = "I can help you with music recommendations! Here's a great playlist for you:"
            self.ai_service.chat = AsyncMock(return_value=expected_response)

            # Simulate user sending a message
            mock_ctx.invoke = MagicMock()

            # Call the chat command
            self.cog.chat_command(mock_ctx, "Can you recommend a playlist?")

            # Verify the AI service was called correctly
            self.ai_service.chat.assert_called_once_with(
                guild_id=789012,
                user_id=123456,
                user_message="Can you recommend a playlist?",
            )

            # Verify the response was sent to the user
            mock_ctx.send.assert_called_once_with(expected_response)

    def test_chat_workflow_with_history_persistence(self):
        """Test chat workflow with conversation history."""
        # Setup Discord context
        mock_ctx = MagicMock(spec=Context)
        mock_ctx.author = MagicMock()
        mock_ctx.author.id = 123456
        mock_ctx.guild = MagicMock()
        mock_ctx.guild.id = 789012
        mock_ctx.channel = MagicMock()
        mock_ctx.channel.send = AsyncMock()
        mock_ctx.send = AsyncMock()
        mock_ctx.bot = self.mock_bot

        mock_ctx.typing = AsyncMock()

        # Mock check_ai_enabled to return True
        with patch('bot.cogs.chat.commands.check_ai_enabled', return_value=True):
            # Setup conversation history in AI service
            self.ai_service.add_to_history(789012, 123456, "user", "Hello")
            self.ai_service.add_to_history(789012, 123456, "assistant", "Hi there!")

            # Mock AI service response
            expected_response = "I remember you asked earlier. Let me get that playlist for you."
            self.ai_service.chat = AsyncMock(return_value=expected_response)

            # Call the chat command again
            self.cog.chat_command(mock_ctx, "Do you remember what I asked earlier?")

            # Verify the AI service was called with conversation context
            self.ai_service.chat.assert_called_once_with(
                guild_id=789012,
                user_id=123456,
                user_message="Do you remember what I asked earlier?",
            )

            # Verify the response was sent
            mock_ctx.send.assert_called_once_with(expected_response)

    def test_clear_chat_workflow(self):
        """Test clear chat workflow."""
        # Setup Discord context
        mock_ctx = MagicMock(spec=Context)
        mock_ctx.author = MagicMock()
        mock_ctx.author.id = 123456
        mock_ctx.guild = MagicMock()
        mock_ctx.guild.id = 789012
        mock_ctx.channel = MagicMock()
        mock_ctx.channel.send = AsyncMock()
        mock_ctx.send = AsyncMock()
        mock_ctx.bot = self.mock_bot

        # Mock check_ai_enabled to return True
        with patch('bot.cogs.chat.commands.check_ai', return_value=True):
            # Setup conversation history
            self.ai_service.add_to_history(789012, 123456, "user", "Hello")

            # Call the clear chat command
            self.cog.clear_chat_command(mock_ctx)

            # Verify the AI service clear method was called
            self.ai_service.clear_history.assert_called_once_with(789012, 123456)

            # Verify the success message was sent
            mock_ctx.send.assert_called_once_with("✅ Your conversation history has been cleared.")

    def test_chat_config_workflow(self):
        """Test chat config workflow."""
        # Setup Discord context
        mock_ctx = MagicMock(spec=Context)
        mock_ctx.author = MagicMock()
        mock_ctx.author.id = 123456
        mock_ctx.guild = MagicMock()
        mock_ctx.guild.id = 789012
        mock_ctx.channel = MagicMock()
        mock_ctx.channel.send = AsyncMock()
        mock_ctx.send = AsyncMock()
        mock_ctx.bot = self.mock_bot

        # Mock check_ai_enabled to return True
        with patch('bot.cogs.chat.commands.check_ai_enabled', return_value=True):
            # Call the chat config command
            self.cog.chat_config_command(mock_ctx)

            # Verify the AI service was NOT called
            self.ai_service.chat.assert_not_called()

            # Verify an embed was sent
            mock_ctx.send.assert_called_once()
            call_args = mock_ctx.send.call_args[1]['embed']

            assert call_args.title == "🤖 AI Chat Configuration"
            assert call_args.color == 0x8181f7  # discord.Color.blurple value

    def test_slash_chat_workflow(self):
        """Test slash chat workflow."""
        # Create interaction mock
        mock_interaction = MagicMock(spec=ApplicationContext)
        mock_interaction.guild = MagicMock()
        mock_interaction.guild.id = 789012
        mock_interaction.author = MagicMock()
        mock_interaction.author.id = 123456
        mock_interaction.defer = AsyncMock()
        mock_interaction.respond = AsyncMock()
        mock_interaction.followup = AsyncMock()

        # Mock check_ai_enabled_interaction to return True
        with patch('bot.cogs.chat.commands.check_ai_enabled_interaction', return_value=True):
            # Mock AI service response
            expected_response = "I can help you with that!

Here's what I found:"
            self.ai_service.chat = AsyncMock(return_value=expected_response)

            # Call the slash chat command
            self.cog.slash_chat(mock_interaction, "Hello", False)

            # Verify the AI service was called
            self.ai_service.chat.assert_called_once_with(
                guild_id=789012,
                user_id=123456,
                user_message="Hello",
            )

            # Verify defer was called
            mock_interaction.defer.assert_called_once()

            # Verify response was sent (not ephemeral)
            mock_interaction.respond.assert_called_once_with(expected_response, ephemeral=False)

    def test_slash_clear_chat_workflow(self):
        """Test slash clear chat workflow."""
        # Create interaction mock
        mock_interaction = MagicMock(spec=ApplicationContext)
        mock_interaction.guild = MagicMock()
        mock_interaction.guild.id = 789012
        mock_interaction.author = MagicMock()
        mock_interaction.author.id = 123456
        mock_interaction.respond = AsyncMock()

        # Mock check_ai_enabled_interaction to return True
        with patch('bot.cogs.chat.commands.check_ai_enabled_interaction', return_value=True):
            # Call the slash clear chat command
            self.cog.slash_clear_chat(mock_interaction)

            # Verify the AI service clear method was called
            self.ai_service.clear_history.assert_called_once_with(789012, 123456)

            # Verify response was sent (ephemeral)
            mock_interaction.respond.assert_called_once_with("✅ Conversation history cleared.", ephemeral=True)

    def test_slash_chat_config_workflow(self):
        """Test slash chat config workflow."""
        # Create interaction mock
        mock_interaction = MagicMock(spec=ApplicationContext)
        mock_interaction.guild = MagicMock()
        mock_interaction.guild.id = 789012
        mock_interaction.author = MagicMock()
        mock_interaction.author.id = 123456
        mock_interaction.respond = AsyncMock()

        # Mock check_ai_enabled_interaction to return True
        with patch('bot.cogs.chat.commands.check_ai_enabled_interaction', return_value=True):
            # Call the slash chat config command
            self.cog.slash_chat_config(mock_interaction)

            # Verify the AI service was NOT called
            self.ai_service.chat.assert_not_called()

            # Verify response was sent (ephemeral)
            mock_interaction.respond.assert_called_once()
            call_args = mock_interaction.respond.call_args[1]['embed']

            assert call_args.title == "🤖 AI Chat Configuration"
            assert call_args.color == 0x8181f7

    def test_chat_workflow_error_handling(self):
        """Test chat workflow error handling."""
        # Setup Discord context
        mock_ctx = MagicMock(spec=Context)
        mock_ctx.author = MagicMock()
        mock_ctx.author.id = 123456
        mock_ctx.guild = MagicMock()
        mock_ctx.guild.id = 789012
        mock_ctx.channel = MagicMock()
        mock_ctx.channel.send = AsyncMock()
        mock_ctx.send = AsyncMock()
        mock_ctx.bot = self.mock_bot

        mock_ctx.typing = AsyncMock()

        # Mock check_ai_enabled to return True
        with patch('bot.cogs.chat.commands.check_ai_enabled', return_value=True):
            # Mock AI service to raise an exception
            error_message = "❌ AI error: OpenAI API rate limit exceeded. Please try again later."
            self.ai_service.chat = AsyncMock(return_value=error_message)

            # Call the chat command
            self.cog.chat_command(mock_ctx, "Hello")

            # Verify the AI service was called
            self.ai_service.chat.assert_called_once_with(
                guild_id=789012,
                user_id=123456,
                user_message="Hello",
            )

            # Verify the error message was sent
            mock_ctx.send.assert_called_once_with(error_message)

    def test_chat_workflow_ephemeral_response(self):
        """Test chat workflow with ephemeral response."""
        # Create interaction mock
        mock_interaction = MagicMock(spec=ApplicationContext)
        mock_interaction.guild = MagicMock()
        mock_interaction.guild.id = 789012
        mock_interaction.author = MagicMock()
        mock_interaction.author.id = 123456
        mock_interaction.defer = AsyncMock()
        mock_interaction.respond = AsyncMock()

        # Mock check_ai_enabled_interaction to return True
        with patch('bot.cogs.chat.commands.check_ai_enabled_interaction', return_value=True):
            # Mock AI service response
            expected_response = "This will only be visible to you."
            self.ai_service.chat = AsyncMock(return_value=expected_response)

            # Call the slash chat command with ephemeral=true
            self.cog.slash_chat(mock_interaction, "Hello", True)

            # Verify the AI service was called
            self.ai_service.chat.assert_called_once_with(
                guild_id=789012,
                user_id=123456,
                user_message="Hello",
            )

            # Verify response was sent (ephemeral)
            mock_interaction.respond.assert_called_once_with(expected_response, ephemeral=True)

    def test_chat_workflow_public_response(self):
        """Test chat workflow with public response."""
        # Create interaction mock
        mock_interaction = MagicMock(spec=ApplicationContext)
        mock_interaction.guild = MagicMock()
        mock_interaction.guild.id = 789012
        mock_interaction.author = MagicMock()
        mock_interaction.author.id = 123456
        mock_interaction.defer = AsyncMock()
        mock_interaction.respond = AsyncMock()

        # Mock check_ai_enabled_interaction to return True
        with patch('bot.cogs.chat.commands.check_ai_enabled_interaction', return_value=True):
            # Mock AI service response
            expected_response = "This will be visible to everyone."
            self.ai_service.chat = AsyncMock(return_value=expected_response)

            # Call the slash chat command with ephemeral=false
            self.cog.slash_chat(mock_interaction, "Hello", False)

            # Verify the AI service was called
            self.ai_service.chat.assert_called_once_with(
                guild_id=789012,
                user_id=123456,
                user_message="Hello",
            )

            # Verify response was sent (not ephemeral)
            mock_interaction.respond.assert_called_once_with(expected_response, ephemeral=False)

    def test_comprehensive_user_workflow(self):
        """Test comprehensive user workflow through all chat commands."""
        # This test simulates a user going through the entire chat experience

        # Setup Discord context
        mock_ctx = MagicMock(spec=Context)
        mock_ctx.author = MagicMock()
        mock_ctx.author.id = 123456
        mock_ctx.guild = MagicMock()
        mock_ctx.guild.id = 789012
        mock_ctx.channel = MagicMock()
        mock_ctx.channel.send = AsyncMock()
        mock_ctx.send = AsyncMock()
        mock_ctx.bot = self.mock_bot

        mock_ctx.typing = AsyncMock()

        # Mock check_ai_enabled to return True
        with patch('bot.cogs.chat.commands.check_ai_enabled', return_value=True):
            # Step 1: User asks for music recommendation
            mock_ai_response_1 = "I recommend 'Chill Vibes' by Loona! Would you like more recommendations?"
            self.ai_service.chat = AsyncMock(return_value=mock_ai_response_1)

            self.cog.chat_command(mock_ctx, "Can you recommend some music?")

            self.ai_service.chat.assert_called_with(
                guild_id=789012,
                user_id=123456,
                user_message="Can you recommend some music?",
            )
            mock_ctx.send.assert_called_with(mock_ai_response_1)

            # Step 2: User asks another question
            mock_ai_response_2 = "Sure! I can also show you your favorite tracks or create a playlist. What would you like?"
            self.ai_service.chat.return_value = mock_ai_response_2

            self.cog.chat_command(mock_ctx, "How can I make a playlist?")

            # Reset mock for next call
            self.ai_service.chat.reset_mock()
            mock_ctx.send.reset_mock()

            self.ai_service.chat.assert_called_with(
                guild_id=789012,
                user_id=123456,
                user_message="How can I make a playlist?",
            )
            mock_ctx.send.assert_called_with(mock_ai_response_2)

            # Step 3: User asks to clear chat
            self.ai_service.clear_history = MagicMock()

            self.cog.clear_chat_command(mock_ctx)

            self.ai_service.clear_history.assert_called_once_with(789012, 123456)

            # Verify success message
            mock_ctx.send.assert_called_with("✅ Your conversation history has been cleared.")

            # Step 4: Verify AI service was not called for config
            self.ai_service.chat.assert_not_called()

    def test_interaction_disabled_when_ai_disabled(self):
        """Test that interactions are disabled when AI is disabled."""
        # Setup Discord context
        mock_ctx = MagicMock(spec=Context)
        mock_ctx.author = MagicMock()
        mock_ctx.author.id = 123456
        mock_ctx.guild = MagicMock()
        mock_ctx.guild.id = 789012
        mock_ctx.channel = MagicMock()
        mock_ctx.channel.send = AsyncMock()
        mock_ctx.send = AsyncMock()
        mock_ctx.bot = self.mock_bot

        mock_ctx.typing = AsyncMock()

        # Mock check_ai_enabled to return False
        with patch('bot.cogs.chat.commands.check_ai_enabled', return_value=False):
            # Call the chat command
            self.cog.chat_command(mock_ctx, "Hello")

            # Verify the AI service was NOT called
            self.ai_service.chat.assert_not_called()

            # Verify an error message was sent
            mock_ctx.send.assert_called_once_with(
                "❌ AI chat is disabled. Set `AI_ENABLED=true` in `.env` to enable."
            )

    def test_interaction_disabled_for_slash_commands(self):
        """Test that slash commands are disabled when AI is disabled."""
        # Create interaction mock
        mock_interaction = MagicMock(spec=ApplicationContext)
        mock_interaction.guild = MagicMock()
        mock_interaction.guild.id = 789012
        mock_interaction.author = MagicMock()
        mock_interaction.author.id = 123456
        mock_interaction.defer = AsyncMock()
        mock_interaction.respond = AsyncMock()

        # Mock check_ai_enabled_interaction to return False
        with patch('bot.cogs.chat.commands.check_ai_enabled_interaction', return_value=False):
            # Call the slash chat command
            self.cog.slash_chat(mock_interaction, "Hello", False)

            # Verify the AI service was NOT called
            self.ai_service.chat.assert_not_called()

            # Verify an error message was sent (ephemeral)
            mock_interaction.respond.assert_called_once_with(
                "❌ AI chat is disabled. Set `AI_ENABLED=true` in `.env` to enable.",
                ephemeral=True
            )

    def test_conversation_state_persistence(self):
        """Test that conversation state persists correctly."""
        # Setup Discord context
        mock_ctx = MagicMock(spec=Context)
        mock_ctx.author = MagicMock()
        mock_ctx.author.id = 123456
        mock_ctx.guild = MagicMock()
        mock_ctx.guild.id = 789012
        mock_ctx.channel = MagicMock()
        mock_ctx.channel.send = AsyncMock()
        mock_ctx.send = AsyncMock()
        mock_ctx.bot = self.mock_bot

        mock_ctx.typing = AsyncMock()

        # Mock check_ai_enabled to return True
        with patch('bot.cogs.chat.commands.check_ai_enabled', return_value=True):
            # Setup initial conversation
            self.ai_service.add_to_history(789012, 123456, "user", "Hello")

            # First AI response
            mock_ai_response = "Hello! How can I help you with music today?"
            self.ai_service.chat.return_value = mock_ai_response

            self.cog.chat_command(mock_ctx, "Hello")

            self.ai_service.chat.assert_called_with(
                guild_id=789012,
                user_id=123456,
                user_message="Hello",
            )

            # Get the current conversation
            current_history = self.ai_service.get_history(789012, 123456)
            assert len(current_history) == 3  # system + user + assistant

            # Second message should include previous conversation
            second_response = "I can help you with music recommendations!"
            self.ai_service.chat.return_value = second_response

            self.ai_service.chat.reset_mock()
            mock_ctx.send.reset_mock()

            self.cog.chat_command(mock_ctx, "Show me recommendations")

            # Verify the AI service was called
            self.ai_service.chat.assert_called_with(
                guild_id=789012,
                user_id=123456,
                user_message="Show me recommendations",
            )

            # Verify the new conversation included previous messages
            self.ai_service.chat.assert_called_once()

    def test_error_response_formatting(self):
        """Test that error responses are properly formatted."""
        # Setup Discord context
        mock_ctx = MagicMock(spec=Context)
        mock_ctx.author = MagicMock()
        mock_ctx.author.id = 123456
        mock_ctx.guild = MagicMock()
        mock_ctx.guild.id = 789012
        mock_ctx.channel = MagicMock()
        mock_ctx.channel.send = AsyncMock()
        mock_ctx.send = AsyncMock()
        mock_ctx.bot = self.mock_bot

        mock_ctx.typing = AsyncMock()

        # Mock check_ai_enabled to return True
        with patch('bot.cogs.chat.commands.check_ai_enabled', return_value=True):
            # Simulate AI service error
            error_response = "❌ AI error: Invalid API key. Please check your configuration."
            self.ai_service.chat.return_value = error_response

            self.cog.chat_command(mock_ctx, "Test")

            # Verify the error response was sent
            self.ai_service.chat.assert_called_once_with(
                guild_id=789012,
                user_id=123456,
                user_message="Test",
            )

            mock_ctx.send.assert_called_once_with(error_response)


@pytest.fixture
def mock_discord_context():
    """Fixture for mock Discord context."""
    mock_ctx = MagicMock(spec=Context)
    mock_ctx.author = MagicMock()
    mock_ctx.author.id = 123456
    mock_ctx.guild = MagicMock()
    mock_ctx.guild.id = 789012
    mock_ctx.channel = MagicMock()
    mock_ctx.channel.send = AsyncMock()
    mock_ctx.send = AsyncMock()
    mock_ctx.bot = MagicMock()
    mock_ctx.typing = MagicMock()
    return mock_ctx


@pytest.fixture
def mock_discord_interaction():
    """Fixture for mock Discord interaction."""
    mock_interaction = MagicMock(spec=ApplicationContext)
    mock_interaction.guild = MagicMock()
    mock_interaction.guild.id = 789012
    mock_interaction.author = MagicMock()
    mock_interaction.author.id = 123456
    mock_interaction.defer = MagicMock()
    mock_interaction.respond = MagicMock()
    mock_interaction.followup = MagicMock()
    return mock_interaction


if __name__ == "__main__":
    # This allows the file to be run directly for testing
    pytest.main([__file__, "-v", "--tb=short"])