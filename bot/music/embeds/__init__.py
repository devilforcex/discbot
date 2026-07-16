"""Embeds package — re-exports submodules for backwards compat."""

from .common import build_progress_bar, format_duration
from .filters import filter_embed
from .help import help_embed
from .library import favorites_embed, playlist_embed
from .player import player_idle_embed, player_now_playing_embed
from .queue import queue_embed
from .search import search_results_embed, track_added

# Explicit re-exports to satisfy linter (F401)
__all__ = [
    "build_progress_bar",
    "format_duration",
    "filter_embed",
    "help_embed",
    "favorites_embed",
    "playlist_embed",
    "player_idle_embed",
    "player_now_playing_embed",
    "queue_embed",
    "search_results_embed",
    "track_added",
]

# Re-export for backwards compatibility
build_progress_bar = build_progress_bar
format_duration = format_duration
filter_embed = filter_embed
help_embed = help_embed
favorites_embed = favorites_embed
playlist_embed = playlist_embed
player_idle_embed = player_idle_embed
player_now_playing_embed = player_now_playing_embed
queue_embed = queue_embed
search_results_embed = search_results_embed
track_added = track_added
