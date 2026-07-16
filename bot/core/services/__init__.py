"""
Core services — auth, voice, playback, AI.

Single source of truth to eliminate duplication.
"""

from .auth import check_authorized, check_authorized_sync_from_bot, is_owner, resolve_user_id
from .playback import play_or_queue_track
from .voice import ensure_voice_player, get_player, voice_check
from .ai_service import AIService, get_ai_service, init_ai_service

__all__ = [
    "check_authorized",
    "check_authorized_sync_from_bot",
    "is_owner",
    "resolve_user_id",
    "ensure_voice_player",
    "get_player",
    "voice_check",
    "play_or_queue_track",
    "AIService",
    "get_ai_service",
    "init_ai_service",
]
