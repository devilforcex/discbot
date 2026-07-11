"""Track search helpers for Lavalink/Wavelink.

The bot accepts simple user-facing source names in SQLite settings while
Wavelink expects TrackSource values or plugin search prefixes. This module keeps
that mapping in one place and provides a small fallback chain so a temporary
YouTube Music load problem does not make `!play` look broken.
"""
from __future__ import annotations

import logging
from typing import Iterable

import wavelink

logger = logging.getLogger(__name__)

URL_PREFIXES = ("http://", "https://")
SOURCE_ALIASES = {
    "yt": wavelink.TrackSource.YouTube,
    "youtube": wavelink.TrackSource.YouTube,
    "ytsearch": wavelink.TrackSource.YouTube,
    "ytm": wavelink.TrackSource.YouTubeMusic,
    "youtube_music": wavelink.TrackSource.YouTubeMusic,
    "ytmsearch": wavelink.TrackSource.YouTubeMusic,
    "sc": wavelink.TrackSource.SoundCloud,
    "soundcloud": wavelink.TrackSource.SoundCloud,
    "scsearch": wavelink.TrackSource.SoundCloud,
}


def is_url(query: str) -> bool:
    return query.strip().lower().startswith(URL_PREFIXES)


def normalize_source(source: str | None):
    """Return a Wavelink source/prefix from a config/database string."""
    if not source:
        return wavelink.TrackSource.YouTubeMusic
    cleaned = str(source).strip().lower().removesuffix(":")
    return SOURCE_ALIASES.get(cleaned, source)


def fallback_sources(preferred: str | None) -> list:
    """Return preferred source plus safe fallbacks, without duplicates."""
    ordered = [
        normalize_source(preferred),
        wavelink.TrackSource.YouTubeMusic,
        wavelink.TrackSource.YouTube,
        wavelink.TrackSource.SoundCloud,
    ]
    result = []
    seen = set()
    for item in ordered:
        key = getattr(item, "value", str(item))
        if key in seen:
            continue
        seen.add(key)
        result.append(item)
    return result


async def search_tracks(query: str, *, source: str | None = None, fallbacks: bool = True):
    """Search Lavalink for a query or URL.

    URLs are resolved without a search source. Text searches use the configured
    source and optionally fall back to YouTube Music, YouTube, then SoundCloud.
    The last Lavalink exception is re-raised if every source fails.
    """
    query = query.strip()
    if not query:
        return []

    if is_url(query):
        return await wavelink.Playable.search(query, source=None)

    sources: Iterable = fallback_sources(source) if fallbacks else [normalize_source(source)]
    last_error: Exception | None = None
    for src in sources:
        try:
            tracks = await wavelink.Playable.search(query, source=src)
            if tracks:
                return tracks
        except Exception as exc:
            last_error = exc
            logger.warning("Track search failed via %s for %r: %s", src, query, exc)
            continue
    if last_error:
        raise last_error
    return []
