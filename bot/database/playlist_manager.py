"""Facade for old import path — actual code in playlists/ package."""

from .playlists import (
    add_track,
    create_playlist,
    delete_playlist,
    get_max_tracks,
    get_playlist,
    list_user_playlists,
    remove_track,
)

__all__ = [
    "create_playlist",
    "get_playlist",
    "list_user_playlists",
    "delete_playlist",
    "add_track",
    "remove_track",
    "get_max_tracks",
]
