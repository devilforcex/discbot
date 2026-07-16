"""
Views package — split from monolithic 894-line file.

Keeps backward compatibility: old imports still work:
from bot.music.views import SearchView, QueuePaginatorView, ...
"""

from .base import (
    auth_ok,
    ensure_voice_player_shared,
    is_url,
    play_wavelink_track_shared,
)
from .base import (
    auth_ok as _auth_ok,
)
from .base import (
    ensure_voice_player_shared as _ensure_voice_player,
)
from .base import (
    is_url as _is_url,
)
from .base import (
    play_wavelink_track_shared as _play_wavelink_track,
)
from .favorites import FavoriteSelect, FavoritesPaginatorView
from .playlists import PlaylistDetailView, PlaylistListView, PlaylistSelect, PlaylistTrackSelect
from .queue import QueuePaginatorView
from .search import SearchView, TrackSelect

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
