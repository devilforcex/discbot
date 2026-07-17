"""
AI Service - Handles all AI interactions via Omniroute/OpenAI-compatible API.
Provides chat completion, conversation management, and context handling.
Supports fallback API keys for rate-limit/credit resilience.
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
        self._conversations: dict[str, list[dict]] = {}  # key: "guild_id:user_id"
        self._base_url: str = ""
        self._api_keys: list[str] = []
        self._default_headers: dict[str, str] | None = None
        self._current_key_index: int = 0
        self._clients: list[AsyncOpenAI] = []

    def _build_config(self) -> None:
        if self.config.ai_provider == "omniroute":
            self._base_url = self.config.omniroute_base_url.rstrip("/")
            keys = [self.config.omniroute_api_key]
            fallback = self.config.omniroute_api_keys_fallback
            if fallback:
                keys.extend(k.strip() for k in fallback.split(",") if k.strip())
            self._api_keys = [k for k in keys if k]
            if not self._api_keys:
                self._api_keys = ["not-needed"]
        else:
            self._base_url = "https://api.openai.com/v1"
            self._api_keys = [self.config.openai_api_key or ""]

        default_headers: dict[str, str] = {}
        if "openrouter.ai" in self._base_url:
            default_headers = {
                "HTTP-Referer": "https://github.com/devilforcex/DrusaBoT",
                "X-Title": "DrusaBoT",
            }
        self._default_headers = default_headers or None

        self._clients = [
            AsyncOpenAI(
                base_url=self._base_url,
                api_key=key,
                timeout=30.0,
                default_headers=self._default_headers,
            )
            for key in self._api_keys
        ]
        self._current_key_index = 0
        logger.info(
            "AI service configured with %d API key(s) for %s",
            len(self._api_keys),
            self._base_url,
        )

    @property
    def client(self) -> AsyncOpenAI:
        if not self._clients:
            self._build_config()
        return self._clients[self._current_key_index]

    def _rotate_key(self) -> bool:
        next_index = (self._current_key_index + 1) % len(self._api_keys)
        if next_index == self._current_key_index:
            return False
        self._current_key_index = next_index
        logger.warning("Rotated to fallback API key #%d", self._current_key_index + 1)
        return True

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

        # Build messages with history
        messages = [{"role": "system", "content": system_prompt or self.config.ai_system_prompt}]
        messages.extend(self.get_history(guild_id, user_id))
        messages.append({"role": "user", "content": user_message})

        # Try each available key on retryable errors (402, 429)
        max_attempts = len(self._api_keys) if self._api_keys else 1
        last_error: Exception | None = None

        for attempt in range(max_attempts):
            try:
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
                last_error = e
                error_str = str(e)
                # Retry on rate-limit (429) or insufficient credits (402)
                is_retryable = "429" in error_str or "402" in error_str
                if is_retryable and self._rotate_key():
                    logger.warning(
                        "Retryable error (attempt %d), rotating API key: %s",
                        attempt + 1,
                        error_str[:150],
                    )
                    continue
                logger.error("AI chat error: %s", e)
                return f"❌ AI error: {str(e)[:200]}"

        return f"❌ AI error: all keys exhausted — {str(last_error)[:150] if last_error else 'unknown'}"


# ────────────────────────────────────────────────────────────────────────


_ai_service: AIService | None = None


def get_ai_service() -> AIService | None:
    return _ai_service


def init_ai_service(config: Config) -> AIService:
    global _ai_service
    _ai_service = AIService(config)
    return _ai_service
