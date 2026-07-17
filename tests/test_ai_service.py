"""Unit tests for AIService."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from bot.core.services.ai_service import AIService


@pytest.fixture
def mock_config():
    config = MagicMock()
    config.ai_enabled = True
    config.ai_provider = "omniroute"
    config.omniroute_base_url = "https://openrouter.ai/api/v1"
    config.omniroute_api_key = "test-key-1"
    config.omniroute_api_keys_fallback = "test-key-2,test-key-3"
    config.openai_api_key = None
    config.ai_default_model = "openai/gpt-oss-20b:free"
    config.ai_system_prompt = "Test prompt"
    config.ai_max_history = 10
    config.ai_temperature = 0.7
    return config


class TestAIServiceInit:
    def test_init(self, mock_config):
        service = AIService(mock_config)
        assert service.config == mock_config
        assert service._conversations == {}
        assert service._clients == []

    def test_build_config_loads_all_keys(self, mock_config):
        service = AIService(mock_config)
        service._build_config()
        assert len(service._api_keys) == 3
        assert service._api_keys[0] == "test-key-1"
        assert service._api_keys[1] == "test-key-2"
        assert service._api_keys[2] == "test-key-3"

    def test_build_config_openrouter_headers(self, mock_config):
        service = AIService(mock_config)
        service._build_config()
        assert service._default_headers is not None
        assert "HTTP-Referer" in service._default_headers
        assert "X-Title" in service._default_headers

    def test_build_config_no_headers_for_non_openrouter(self, mock_config):
        mock_config.omniroute_base_url = "http://localhost:20128/v1"
        service = AIService(mock_config)
        service._build_config()
        assert service._default_headers is None

    def test_build_config_openai_provider(self, mock_config):
        mock_config.ai_provider = "openai"
        mock_config.openai_api_key = "sk-openai"
        service = AIService(mock_config)
        service._build_config()
        assert "api.openai.com" in service._base_url
        assert len(service._api_keys) == 1


class TestAIServiceHistory:
    def test_get_history_empty(self, mock_config):
        service = AIService(mock_config)
        assert service.get_history(123, 456) == []

    def test_add_and_get_history(self, mock_config):
        service = AIService(mock_config)
        service.add_to_history(123, 456, "user", "hello")
        service.add_to_history(123, 456, "assistant", "hi there")
        history = service.get_history(123, 456)
        assert len(history) == 2
        assert history[0] == {"role": "user", "content": "hello"}
        assert history[1] == {"role": "assistant", "content": "hi there"}

    def test_clear_history(self, mock_config):
        service = AIService(mock_config)
        service.add_to_history(123, 456, "user", "hello")
        service.clear_history(123, 456)
        assert service.get_history(123, 456) == []

    def test_history_isolated_per_user(self, mock_config):
        service = AIService(mock_config)
        service.add_to_history(123, 456, "user", "user1 msg")
        service.add_to_history(123, 789, "user", "user2 msg")
        assert len(service.get_history(123, 456)) == 1
        assert len(service.get_history(123, 789)) == 1

    def test_history_trimmed(self, mock_config):
        mock_config.ai_max_history = 2
        service = AIService(mock_config)
        for i in range(10):
            service.add_to_history(123, 456, "user", f"msg {i}")
            service.add_to_history(123, 456, "assistant", f"resp {i}")
        history = service.get_history(123, 456)
        assert len(history) == 4  # 2 pairs * 2


class TestAIServiceKeyRotation:
    def test_rotate_key(self, mock_config):
        service = AIService(mock_config)
        service._build_config()
        assert service._current_key_index == 0
        assert service._rotate_key() is True
        assert service._current_key_index == 1
        assert service._rotate_key() is True
        assert service._current_key_index == 2
        assert service._rotate_key() is True
        assert service._current_key_index == 0  # wraps around

    def test_rotate_key_single_key(self, mock_config):
        mock_config.omniroute_api_keys_fallback = ""
        service = AIService(mock_config)
        service._build_config()
        assert service._rotate_key() is False


class TestAIServiceChat:
    @pytest.mark.asyncio
    async def test_chat_disabled(self, mock_config):
        mock_config.ai_enabled = False
        service = AIService(mock_config)
        result = await service.chat(123, 456, "hello")
        assert "disabled" in result.lower()

    @pytest.mark.asyncio
    async def test_chat_success(self, mock_config):
        service = AIService(mock_config)
        service._build_config()

        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=MagicMock(content="Hello!"))]

        with patch.object(service._clients[0], "chat") as mock_chat:
            mock_chat.completions.create = AsyncMock(return_value=mock_response)
            result = await service.chat(123, 456, "Say hi")
            assert result == "Hello!"

    @pytest.mark.asyncio
    async def test_chat_stores_history(self, mock_config):
        service = AIService(mock_config)
        service._build_config()

        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=MagicMock(content="Response!"))]

        with patch.object(service._clients[0], "chat") as mock_chat:
            mock_chat.completions.create = AsyncMock(return_value=mock_response)
            await service.chat(123, 456, "question")
            history = service.get_history(123, 456)
            assert len(history) == 2
            assert history[0]["role"] == "user"
            assert history[1]["role"] == "assistant"

    @pytest.mark.asyncio
    async def test_chat_error_returns_message(self, mock_config):
        service = AIService(mock_config)
        service._build_config()

        with patch.object(service._clients[0], "chat") as mock_chat:
            mock_chat.completions.create = AsyncMock(side_effect=Exception("API down"))
            result = await service.chat(123, 456, "question")
            assert "error" in result.lower()

    @pytest.mark.asyncio
    async def test_chat_rotates_on_429(self, mock_config):
        service = AIService(mock_config)
        service._build_config()

        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=MagicMock(content="OK from key 2"))]

        error_429 = Exception("Error code: 429 - rate limited")

        with patch.object(service._clients[0], "chat") as mock_chat_0, \
             patch.object(service._clients[1], "chat") as mock_chat_1:
            mock_chat_0.completions.create = AsyncMock(side_effect=error_429)
            mock_chat_1.completions.create = AsyncMock(return_value=mock_response)
            result = await service.chat(123, 456, "question")
            assert result == "OK from key 2"
            assert service._current_key_index == 1

    @pytest.mark.asyncio
    async def test_chat_rotates_on_402(self, mock_config):
        service = AIService(mock_config)
        service._build_config()

        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=MagicMock(content="OK from key 2"))]

        error_402 = Exception("Error code: 402 - insufficient credits")

        with patch.object(service._clients[0], "chat") as mock_chat_0, \
             patch.object(service._clients[1], "chat") as mock_chat_1:
            mock_chat_0.completions.create = AsyncMock(side_effect=error_402)
            mock_chat_1.completions.create = AsyncMock(return_value=mock_response)
            result = await service.chat(123, 456, "question")
            assert result == "OK from key 2"
