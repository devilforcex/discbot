"""Embeds package — re-exports submodules for backwards compat."""
from .common import build_progress_bar, format_duration
from .player import player_idle_embed, player_now_playing_embed
from .queue import queue_embed
from .library import favorites_embed, playlist_embed
from .search import search_results_embed, track_added
from .filters import filter_embed
from .help import help_embed
