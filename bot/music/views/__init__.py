"""
Views package — split from monolithic 894-line file.

Keeps backward compatibility: old imports still work:
from bot.music.views import SearchView, QueuePaginatorView, ...
"""

from .base import (
    is_url,
    auth_ok,
    ensure_voice_player_shared,
    play_wavelink_track_shared,
    is_url as _is_url,
    auth_ok as _auth_ok,
    ensure_voice_player_shared as _ensure_voice_player,
    play_wavelink_track_shared as _play_wavelink_track,
)
from .search import SearchView, TrackSelect
from .queue import QueuePaginatorView
from .favorites import FavoriteSelect, FavoritesPaginatorView
from .playlists import PlaylistDetailView, PlaylistListView, PlaylistSelect, PlaylistTrackSelect

__all__ = [
    "is_url",
    "_is_url",
    "auth_ok",
    "_auth_ok",
    "ensure_voice_player_shared",
    "_ensure_voice_player",
    "play_wavelink_track_shared",
    "_play_wavelink_track",
    "SearchView",
    "TrackSelect",
    "QueuePaginatorView",
    "FavoriteSelect",
    "FavoritesPaginatorView",
    "PlaylistDetailView",
    "PlaylistListView",
    "PlaylistSelect",
    "PlaylistTrackSelect",
]
