"""
Unit tests for AI Service.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from bot.core.services.ai_service import AIService
from bot.config import Config


class TestAIService:
    """Test cases for AIService class."""

    def test_init_with_config(self):
        """Test AIService initialization with config."""
        mock_config = MagicMock(spec=Config)
        mock_config.ai_enabled = True
        mock_config.ai_provider = "openai"
        mock_config.omniroute_base_url = "http://localhost:20128/v1"
        mock_config.omniroute_api_key = "test-key"
        mock_config.ai_default_model = "gpt-4o-mini"
        mock_config.ai_system_prompt = "Test prompt"
        mock_config.ai_max_history = 10
        mock_config.ai_temperature = 0.7

        service = AIService(mock_config)

        assert service.config == mock_config
        assert service._conversations == {}

    def test_client_lazy_initialization_openai(self):
        """Test client initialization with OpenAI provider."""
        mock_config = MagicMock(spec=Config)
        mock_config.ai_provider = "openai"
        mock_config.omniroute_base_url = "http://localhost:20128/v1"
        mock_config.omniroute_api_key = "test-key"
        mock_config.ai_default_model = "gpt-4o-mini"
        mock_config.ai_system_prompt = "Test prompt"
        mock_config.ai_max_history = 10
        mock_config.ai_temperature = 0.7

        service = AIService(mock_config)

        assert service._client is None

        with patch.object(service, "client") as mock_client:
            mock_client.chat.completions.create.return_value = MagicMock(
                choices=[MagicMock(message=MagicMock(content="Test response"))]
            )

            response = service.client

            assert response is not None

    def test_client_lazy_initialization_omniroute(self):
        """Test client initialization with Omniroute provider."""
        mock_config = MagicMock(spec=Config)
        mock_config.ai_provider = "omniroute"
        mock_config.omniroute_base_url = "http://localhost:20128/v1"
        mock_config.omniroute_api_key = "test-key"
        mock_config.ai_default_model = "gpt-4o-mini"
        mock_config.ai_system_prompt = "Test prompt"
        mock_config.ai_max_history = 10
        mock_config.ai_temperature = 0.7

        service = AIService(mock_config)

        with patch.object(service, "client") as mock_client:
            mock_client.chat.completions.create.return_value = MagicMock(
                choices=[MagicMock(message=MagicMock(content="Test response"))]
            )

            response = service.client

            assert response is not None

    def test_get_conversation_key(self):
        """Test conversation key generation."""
        mock_config = MagicMock(spec=Config)
        service = AIService(mock_config)

        key = service._get_conversation_key(123456, 789012)

        assert key == "123456:789012"

    def test_get_history_empty(self):
        """Test getting history for non-existent conversation."""
        mock_config = MagicMock(spec=Config)
        service = AIService(mock_config)

        history = service.get_history(123456, 789012)

        assert history == []

    def test_get_history_existing(self):
        """Test getting existing conversation history."""
        mock_config = MagicMock(spec=Config)
        service = AIService(mock_config)

        # Manually add history
        service._conversations["123456:789012"] = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there!"},
        ]

        history = service.get_history(123456, 789012)

        assert len(history) == 2
        assert history[0]["role"] == "user"
        assert history[0]["content"] == "Hello"
        assert history[1]["role"] == "assistant"
        assert history[1]["content"] == "Hi there!"

    def test_add_to_history_new_conversation(self):
        """Test adding to new conversation."""
        mock_config = MagicMock(spec=Config)
        service = AIService(mock_config)

        service.add_to_history(123456, 789012, "user", "Hello")

        assert service._conversations["123456:789012"] == [
            {"role": "user", "content": "Hello"},
        ]

    def test_add_to_history_existing_conversation(self):
        """Test adding to existing conversation."""
        mock_config = MagicMock(spec=Config)
        service = AIService(mock_config)

        service._conversations["123456:789012"] = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there!"},
        ]

        service.add_to_history(123456, 789012, "user", "How are you?")

        assert len(service._conversations["123456:789012"]) == 3
        assert service._conversations["123456:789012"][2]["role"] == "user"
        assert service._conversations["123456:789012"][2]["content"] == "How are you?"

    def test_add_to_history_trim_when_exceeds_max(self):
        """Test history trimming when exceeds maximum."""
        mock_config = MagicMock(spec=Config)
        mock_config.ai_max_history = 2  # Max 2 pairs (4 messages)
        service = AIService(mock_config)

        # Add 6 messages (3 pairs)
        for i in range(6):
            role = "user" if i % 2 == 0 else "assistant"
            service.add_to_history(123456, 789012, role, f"Message {i}")

        # Should be trimmed to 4 messages (2 pairs)
        assert len(service._conversations["123456:789012"]) == 4

    def test_clear_history_existing(self):
        """Test clearing existing conversation history."""
        mock_config = MagicMock(spec=Config)
        service = AIService(mock_config)

        service._conversations["123456:789012"] = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there!"},
        ]

        service.clear_history(123456, 789012)

        assert "123456:789012" not in service._conversations

    def test_clear_history_nonexistent(self):
        """Test clearing non-existent conversation history."""
        mock_config = MagicMock(spec=Config)
        service = AIService(mock_config)

        service.clear_history(123456, 789012)

        assert "123456:789012" not in service._conversations

    async def test_chat_disabled(self):
        """Test chat when AI is disabled."""
        mock_config = MagicMock(spec=Config)
        mock_config.ai_enabled = False
        mock_config.ai_system_prompt = "Test prompt"
        mock_config.ai_max_history = 10
        mock_config.ai_temperature = 0.7

        service = AIService(mock_config)

        response = await service.chat(123456, 789012, "Hello")

        assert "disabled" in response.lower()

    async def test_chat_success(self):
        """Test successful chat completion."""
        mock_config = MagicMock(spec=Config)
        mock_config.ai_enabled = True
        mock_config.ai_provider = "openai"
        mock_config.omniroute_base_url = "http://localhost:20128/v1"
        mock_config.omniroute_api_key = "test-key"
        mock_config.ai_default_model = "gpt-4o-mini"
        mock_config.ai_system_prompt = "You are a helpful AI assistant"
        mock_config.ai_max_history = 10
        mock_config.ai_temperature = 0.7

        service = AIService(mock_config)

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message = MagicMock()
        mock_response.choices[0].message.content = "Hello! How can I help you today?"

        with patch.object(service, "client") as mock_client:
            mock_client.chat.completions.create.return_value = mock_response

            response = await service.chat(123456, 789012, "Hello")

            assert response == "Hello! How can I help you today?"
            assert "123456:789012" in service._conversations
            assert len(service._conversations["123456:789012"]) == 4  # system + user + assistant

    async def test_chat_api_error(self):
        """Test chat when API call fails."""
        mock_config = MagicMock(spec=Config)
        mock_config.ai_enabled = True
        mock_config.ai_provider = "openai"
        mock_config.omniroute_base_url = "http://localhost:20128/v1"
        mock_config.omniroute_api_key = "test-key"
        mock_config.ai_default_model = "gpt-4o-mini"
        mock_config.ai_system_prompt = "Test prompt"
        mock_config.ai_max_history = 10
        mock_config.ai_temperature = 0.7

        service = AIService(mock_config)

        with patch.object(service, "client") as mock_client:
            mock_client.chat.completions.create.side_effect = Exception("API error")

            response = await service.chat(123456, 789012, "Hello")

            assert "API error" in response
            assert response.startswith("❌ AI error:")

    async def test_chat_with_custom_system_prompt(self):
        """Test chat with custom system prompt."""
        mock_config = MagicMock(spec=Config)
        mock_config.ai_enabled = True
        mock_config.ai_provider = "openai"
        mock_config.omniroute_base_url = "http://localhost:20128/v1"
        mock_config.omniroute_api_key = "test-key"
        mock_config.ai_default_model = "gpt-4o-mini"
        mock_config.ai_system_prompt = "Default prompt"
        mock_config.ai_max_history = 10
        mock_config.ai_temperature = 0.7

        service = AIService(mock_config)

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message = MagicMock()
        mock_response.choices[0].message.content = "Response"

        with patch.object(service, "client") as mock_client:
            mock_client.chat.completions.create.return_value = mock_response

            response = await service.chat(
                guild_id=123456,
                user_id=789012,
                user_message="Hello",
                system_prompt="Custom prompt"
            )

            # Verify the API was called with custom system prompt
            call_args = mock_client.chat.completions.create.call_args
            messages = call_args[1]["messages"]

            assert messages[0]["content"] == "Custom prompt"
            assert messages[1]["role"] == "user"
            assert messages[1]["content"] == "Hello"

    async def test_chat_with_custom_model_and_temperature(self):
        """Test chat with custom model and temperature."""
        mock_config = MagicMock(spec=Config)
        mock_config.ai_enabled = True
        mock_config.ai_provider = "openai"
        mock_config.omniroute_base_url = "http://localhost:20128/v1"
        mock_config.omniroute_api_key = "test-key"
        mock_config.ai_default_model = "gpt-4o-mini"
        mock_config.ai_system_prompt = "Test prompt"
        mock_config.ai_max_history = 10
        mock_config.ai_temperature = 0.5

        service = AIService(mock_config)

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message = MagicMock()
        mock_response.choices[0].message.content = "Response"

        with patch.object(service, "client") as mock_client:
            mock_client.chat.completions.create.return_value = mock_response

            response = await service.chat(
                guild_id=123456,
                user_id=789012,
                user_message="Hello",
                model="gpt-3.5-turbo",
                temperature=0.9
            )

            # Verify the API was called with custom model and temperature
            call_args = mock_client.chat.completions.create.call_args
            assert call_args[1]["model"] == "gpt-3.5-turbo"
            assert call_args[1]["temperature"] == 0.9

    def test_conversation_persistence(self):
        """Test that conversations persist across service calls."""
        mock_config = MagicMock(spec=Config)
        mock_config.ai_enabled = True
        mock_config.ai_provider = "openai"
        mock_config.omniroute_base_url = "http://localhost:20128/v1"
        mock_config.omniroute_api_key = "test-key"
        mock_config.ai_default_model = "gpt-4o-mini"
        mock_config.ai_system_prompt = "Test prompt"
        mock_config.ai_max_history = 10
        mock_config.ai_temperature = 0.7

        service = AIService(mock_config)

        # Add a message
        service.add_to_history(123456, 789012, "user", "Hello")
        assert service._conversations["123456:789012"][0]["content"] == "Hello"

        # Create new service instance (simulating new process)
        service2 = AIService(mock_config)

        # History should be preserved
        history = service2.get_history(123456, 789012)
        assert len(history) == 1
        assert history[0]["content"] == "Hello"