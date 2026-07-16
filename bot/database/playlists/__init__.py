"""Playlists package facade."""

from .crud import create_playlist, delete_playlist, get_playlist, list_user_playlists
from .tracks import add_track, get_max_tracks, remove_track

__all__ = [
    "create_playlist",
    "get_playlist",
    "list_user_playlists",
    "delete_playlist",
    "add_track",
    "remove_track",
    "get_max_tracks",
]
