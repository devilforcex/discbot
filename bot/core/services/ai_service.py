"""
AI Service - Handles all AI interactions via Omniroute/OpenAI-compatible API.
Provides chat completion, conversation management, and context handling.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from openai import AsyncOpenAI

if TYPE_CHECKING:
    from bot.config import Config

logger = logging.getLogger(__name__)


# ────────────────────────────────────────────────────────────────────────


class AIService:
    """Manages AI chat interactions with conversation history."""

    def __init__(self, config: Config):
        self.config = config
        self._client: AsyncOpenAI | None = None
        self._conversations: dict[str, list[dict]] = {}  # key: "guild_id:user_id"

    @property
    def client(self) -> AsyncOpenAI:
        if self._client is None:
            if self.config.ai_provider == "omniroute":
                base_url = self.config.omniroute_base_url.rstrip("/")
                api_key = self.config.omniroute_api_key or "not-needed"
            else:
                base_url = "https://api.openai.com/v1"
                api_key = self.config.openai_api_key or ""

            self._client = AsyncOpenAI(
                base_url=base_url,
                api_key=api_key,
                timeout=30.0,
            )
        return self._client

    def _get_conversation_key(self, guild_id: int, user_id: int) -> str:
        return f"{guild_id}:{user_id}"

    def get_history(self, guild_id: int, user_id: int) -> list[dict]:
        key = self._get_conversation_key(guild_id, user_id)
        return self._conversations.get(key, [])

    def add_to_history(self, guild_id: int, user_id: int, role: str, content: str) -> None:
        key = self._get_conversation_key(guild_id, user_id)
        history = self._conversations.setdefault(key, [])
        history.append({"role": role, "content": content})
        # Trim to max history (pairs of user+assistant)
        max_hist = self.config.ai_max_history * 2
        if len(history) > max_hist:
            self._conversations[key] = history[-max_hist:]

    def clear_history(self, guild_id: int, user_id: int) -> None:
        key = self._get_conversation_key(guild_id, user_id)
        self._conversations.pop(key, None)

    async def chat(
        self,
        guild_id: int,
        user_id: int,
        user_message: str,
        system_prompt: str | None = None,
        model: str | None = None,
        temperature: float | None = None,
    ) -> str:
        """Send a chat message and get AI response with conversation context."""
        if not self.config.ai_enabled:
            return "❌ AI chat is disabled. Enable it in config (AI_ENABLED=true)."

        try:
            # Build messages with history
            messages = [{"role": "system", "content": system_prompt or self.config.ai_system_prompt}]
            messages.extend(self.get_history(guild_id, user_id))
            messages.append({"role": "user", "content": user_message})

            # Call API
            response = await self.client.chat.completions.create(
                model=model or self.config.ai_default_model,
                messages=messages,
                temperature=temperature or self.config.ai_temperature,
                max_tokens=1500,
            )

            assistant_content = response.choices[0].message.content or ""

            # Store in history
            self.add_to_history(guild_id, user_id, "user", user_message)
            self.add_to_history(guild_id, user_id, "assistant", assistant_content)

            return assistant_content

        except Exception as e:
            logger.error("AI chat error: %s", e)
            return f"❌ AI error: {str(e)[:200]}"


# ────────────────────────────────────────────────────────────────────────


_ai_service: AIService | None = None


def get_ai_service() -> AIService | None:
    return _ai_service


def init_ai_service(config: Config) -> AIService:
    global _ai_service
    _ai_service = AIService(config)
    return _ai_service