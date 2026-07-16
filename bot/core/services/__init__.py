"""
Core services — auth, voice, playback.

Single source of truth to eliminate duplication.
"""

from .auth import check_authorized, check_authorized_sync_from_bot, is_owner, resolve_user_id
from .playback import play_or_queue_track
from .voice import ensure_voice_player, get_player, voice_check

__all__ = [
    "check_authorized",
    "check_authorized_sync_from_bot",
    "is_owner",
    "resolve_user_id",
    "ensure_voice_player",
    "get_player",
    "voice_check",
    "play_or_queue_track",
]
