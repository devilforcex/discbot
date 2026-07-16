"""
Integration tests for AI chat commands.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from discord.ext import commands
from bot.cogs.chat.commands import ChatCog


class TestChatCommandsIntegration:
    """Test integration for chat commands."""

    def setup_method(self):
        """Setup test fixtures."""
        self.mock_bot = MagicMock(spec=commands.Bot)
        self.mock_config = MagicMock()
        self.mock_config.ai_enabled = True
        self.mock_config.ai_default_model = "gpt-4o-mini"
        self.mock_config.ai_max_history = 10
        self.mock_config.ai_provider = "openai"
        self.mock_config.omniroute_base_url = "http://localhost:20128/v1"
        self.mock_config.ai_temperature = 0.7

        self.mock_ai_service = MagicMock()
        self.mock_ai_service.chat = AsyncMock()
        self.mock_ai_service.clear_history = MagicMock()

        with patch('bot.cogs.chat.commands.get_config', return_value=self.mock_config):
            with patch('bot.cogs.chat.commands.get_ai_service', return_value=self.mock_ai_service):
                self.cog = ChatCog(self.mock_bot)

    def test_chat_command_enabled(self):
        """Test chat command when AI is enabled."""
        mock_ctx = MagicMock()
        mock_ctx.author.id = 123456
        mock_ctx.guild.id = 789012
        mock_ctx.typing = AsyncMock()
        mock_ctx.send = AsyncMock()
        mock_ctx.bot.loop = MagicMock()

        # Mock check_ai_enabled to return True
        with patch('bot.cogs.chat.commands.check_ai_enabled', return_value=True):
            # Mock the AI service response
            self.mock_ai_service.chat.return_value = "Hello! How can I help you today?"

            # Call the command
            self.cog.chat_command(mock_ctx, "Hello")

            # Verify the AI service was called
            self.mock_ai_service.chat.assert_called_once_with(
                guild_id=789012,
                user_id=123456,
                user_message="Hello",
            )

    def test_chat_command_disabled(self):
        """Test chat command when AI is disabled."""
        mock_ctx = MagicMock()
        mock_ctx.author.id = 123456
        mock_ctx.guild.id = 789012
        mock_ctx.typing = AsyncMock()
        mock_ctx.send = AsyncMock()
        mock_ctx.bot.loop = MagicMock()

        # Mock check_ai_enabled to return False
        with patch('bot.cogs.chat.commands.check_ai_enabled', return_value=False):
            # Call the command
            self.cog.chat_command(mock_ctx, "Hello")

            # Verify the AI service was NOT called
            self.mock_ai_service.chat.assert_not_called()

    def test_clear_chat_command(self):
        """Test clear chat command."""
        mock_ctx = MagicMock()
        mock_ctx.author.id = 123456
        mock_ctx.guild.id = 789012
        mock_ctx.send = AsyncMock()

        # Mock check_ai_enabled to return True
        with patch('bot.cogs.chat.commands.check_ai_enabled', return_value=True):
            # Call the command
            self.cog.clear_chat_command(mock_ctx)

            # Verify the AI service clear method was called
            self.mock_ai_service.clear_history.assert_called_once_with(789012, 123456)

    def test_chat_config_command(self):
        """Test chat config command."""
        mock_ctx = MagicMock()
        mock_ctx.send = AsyncMock()

        # Mock check_ai_enabled to return True
        with patch('bot.cogs.chat.commands.check_ai_enabled', return_value=True):
            # Call the command
            self.cog.chat_config_command(mock_ctx)

            # Verify the AI service was NOT called
            self.mock_ai_service.chat.assert_not_called()

    def test_slash_chat_command(self):
        """Test slash chat command."""
        mock_interaction = MagicMock()
        mock_interaction.guild.id = 789012
        mock_interaction.author.id = 123456
        mock_interaction.defer = AsyncMock()
        mock_interaction.respond = AsyncMock()

        # Mock check_ai_enabled_interaction to return True
        with patch('bot.cogs.chat.commands.check_ai_enabled_interaction', return_value=True):
            # Mock the AI service response
            self.mock_ai_service.chat.return_value = "Hello! How can I help you today?"

            # Call the command
            self.cog.slash_chat(mock_interaction, "Hello", False)

            # Verify the AI service was called
            self.mock_ai_service.chat.assert_called_once_with(
                guild_id=789012,
                user_id=123456,
                user_message="Hello",
            )

    def test_slash_clear_chat_command(self):
        """Test slash clear chat command."""
        mock_interaction = MagicMock()
        mock_interaction.guild.id = 789012
        mock_interaction.author.id = 123456
        mock_interaction.respond = AsyncMock()

        # Mock check_ai_enabled_interaction to return True
        with patch('bot.cogs.chat.commands.check_ai_enabled_interaction', return_value=True):
            # Call the command
            self.cog.slash_clear_chat(mock_interaction)

            # Verify the AI service clear method was called
            self.mock_ai_service.clear_history.assert_called_once_with(789012, 123456)

    def test_slash_chat_config_command(self):
        """Test slash chat config command."""
        mock_interaction = MagicMock()
        mock_interaction.guild.id = 789012
        mock_interaction.author.id = 123456
        mock_interaction.respond = AsyncMock()

        # Mock check_ai_enabled_interaction to return True
        with patch('bot.cogs.chat.commands.check_ai_enabled_interaction', return_value=True):
            # Call the command
            self.cog.slash_chat_config(mock_interaction)

            # Verify the AI service was NOT called
            self.mock_ai_service.chat.assert_not_called()

    def test_chat_command_with_private_response(self):
        """Test chat command with ephemeral response."""
        mock_interaction = MagicMock()
        mock_interaction.guild.id = 789012
        mock_interaction.author.id = 123456
        mock_interaction.defer = AsyncMock()
        mock_interaction.respond = AsyncMock(ephemeral=True)

        # Mock check_ai_enabled_interaction to return True
        with patch('bot.cogs.chat.commands.check_ai_enabled_interaction', return_value=True):
            # Mock the AI service response
            self.mock_ai_service.chat.return_value = "Hello! How can I help you today?"

            # Call the command
            self.cog.slash_chat(mock_interaction, "Hello", True)

            # Verify the AI service was called
            self.mock_ai_service.chat.assert_called_once_with(
                guild_id=789012,
                user_id=123456,
                user_message="Hello",
            )

    def test_chat_command_response_splitting(self):
        """Test that long responses are split into chunks."""
        mock_ctx = MagicMock()
        mock_ctx.author.id = 123456
        mock_ctx.guild.id = 789012
        mock_ctx.typing = AsyncMock()
        mock_ctx.send = AsyncMock()
        mock_ctx.bot.loop = MagicMock()

        # Mock check_ai_enabled to return True
        with patch('bot.cogs.chat.commands.check_ai_enabled', return_value=True):
            # Mock the AI service response
            long_response = "This is a very long response. " * 50  # Make it longer than 1900 chars
            self.mock_ai_service.chat.return_value = long_response

            # Call the command
            self.cog.chat_command(mock_ctx, "Hello")

            # Verify send was called multiple times for long responses
            assert mock_ctx.send.call_count > 1

    def test_chat_command_ai_service_error_handling(self):
        """Test chat command when AI service returns an error."""
        mock_ctx = MagicMock()
        mock_ctx.author.id = 123456
        mock_ctx.guild.id = 789012
        mock_ctx.typing = AsyncMock()
        mock_ctx.send = AsyncMock()
        mock_ctx.bot.loop = MagicMock()

        # Mock check_ai_enabled to return True
        with patch('bot.cogs.chat.commands.check_ai_enabled', return_value=True):
            # Mock the AI service response
            self.mock_ai_service.chat.return_value = "❌ AI error: Rate limit exceeded."

            # Call the command
            self.cog.chat_command(mock_ctx, "Hello")

            # Verify the AI service was called
            self.mock_ai_service.chat.assert_called_once_with(
                guild_id=789012,
                user_id=123456,
                user_message="Hello",
            )

    def test_chat_command_private_response_ephemeral(self):
        """Test chat command with ephemeral response."""
        mock_interaction = MagicMock()
        mock_interaction.guild.id = 789012
        mock_interaction.author.id = 123456
        mock_interaction.defer = AsyncMock()
        mock_interaction.respond = AsyncMock(ephemeral=True)

        # Mock check_ai_enabled_interaction to return True
        with patch('bot.cogs.chat.commands.check_ai_enabled_interaction', return_value=True):
            # Mock the AI service response
            self.mock_ai_service.chat.return_value = "Hello! How can I help you today?"

            # Call the command
            self.cog.slash_chat(mock_interaction, "Hello", True)

            # Verify the AI service was called
            self.mock_ai_service.chat.assert_called_once_with(
                guild_id=789012,
                user_id=123456,
                user_message="Hello",
            )

    def test_chat_command_private_response_public(self):
        """Test chat command with public response."""
        mock_interaction = MagicMock()
        mock_interaction.guild.id = 789012
        mock_interaction.author.id = 123456
        mock_interaction.defer = AsyncMock()
        mock_interaction.respond = AsyncMock(ephemeral=False)

        # Mock check_ai_enabled_interaction to return True
        with patch('bot.cogs.chat.commands.check_ai_enabled_interaction', return_value=True):
            # Mock the AI service response
            self.mock_ai_service.chat.return_value = "Hello! How can I help you today?"

            # Call the command
            self.cog.slash_chat(mock_interaction, "Hello", False)

            # Verify the AI service was called
            self.mock_ai_service.chat.assert_called_once_with(
                guild_id=789012,
                user_id=123456,
                user_message="Hello",
            )

    def test_chat_command_missing_ai_service(self):
        """Test chat command when AI service is not initialized."""
        mock_ctx = MagicMock()
        mock_ctx.author.id = 123456
        mock_ctx.guild.id = 789012
        mock_ctx.typing = AsyncMock()
        mock_ctx.send = AsyncMock()
        mock_ctx.bot.loop = MagicMock()

        # Mock check_ai_enabled to return True
        with patch('bot.cogs.chat.commands.check_ai_enabled', return_value=True):
            with patch('bot.cogs.chat.commands.get_ai_service', return_value=None):
                # Call the command
                self.cog.chat_command(mock_ctx, "Hello")

                # Verify the AI service was NOT called
                self.mock_ai_service.chat.assert_not_called()
                # Send error message
                mock_ctx.send.assert_called_once()


@pytest.fixture
def mock_discord_context():
    """Fixture for mock Discord context."""
    mock_ctx = MagicMock()
    mock_ctx.author = MagicMock()
    mock_ctx.author.id = 123456
    mock_ctx.guild = MagicMock()
    mock_ctx.guild.id = 789012
    mock_ctx.typing = MagicMock()
    mock_ctx.send = MagicMock()
    mock_ctx.bot = MagicMock()
    return mock_ctx


@pytest.fixture
def mock_discord_interaction():
    """Fixture for mock Discord interaction."""
    mock_interaction = MagicMock()
    mock_interaction.guild = MagicMock()
    mock_interaction.guild.id = 789012
    mock_interaction.author = MagicMock()
    mock_interaction.author.id = 123456
    mock_interaction.defer = MagicMock()
    mock_interaction.respond = MagicMock()
    return mock_interaction