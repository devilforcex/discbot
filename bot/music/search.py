"""
Track search helpers for Lavalink/Wavelink.

The bot accepts simple user-facing source names in SQLite settings while
Wavelink expects TrackSource values or plugin search prefixes. This module keeps
that mapping in one place and provides a small fallback chain so a temporary
YouTube Music load problem does not make `!play` look broken.
"""

from __future__ import annotations

import logging
from collections.abc import Iterable

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
    """Check if the query is a URL."""
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


def _extract_lavalink_error(exc: Exception) -> tuple[str, str]:  # pyright: ignore[reportUnusedFunction]
    """Extract user-friendly error message and cause from LavalinkLoadException.

    Returns:
        Tuple of (user_message, technical_cause)
    """
    if isinstance(exc, wavelink.LavalinkLoadException):
        error_msg = exc.error or "Unknown error"
        cause = exc.cause or "unknown"

        # Map common causes to user-friendly messages
        if "age" in cause.lower() or "restricted" in error_msg.lower():
            return ("Cannot play this track. It may be age-restricted or region-locked.", cause)
        if "copyright" in error_msg.lower() or "unavailable" in error_msg.lower():
            return ("This track is unavailable due to copyright restrictions.", cause)
        if "not found" in error_msg.lower() or "404" in cause.lower():
            return ("Track not found. The URL may be invalid or the content removed.", cause)

        return (error_msg, cause)

    if isinstance(exc, wavelink.NodeException):
        return (f"Failed to connect to Lavalink (status {exc.status}).", "node_connection")

    return (str(exc), "unknown")


async def search_tracks(query: str, *, source: str | None = None, fallbacks: bool = True):
    """Search Lavalink for a query or URL.

    URLs are resolved without a search source. Text searches use the configured
    source and optionally fall back to YouTube Music, YouTube, then SoundCloud.
    The last Lavalink exception is re-raised if every source fails.

    For URLs, if the initial load fails (e.g., YouTube Music can't handle the URL),
    we try alternative sources as fallback to improve reliability.
    """
    query = query.strip()
    if not query:
        return []

    # URL handling - try with fallback if initial source fails
    if is_url(query):
        last_error: Exception | None = None

        # For URLs, try without source first (let Lavalink auto-detect)
        # If that fails, try explicit sources as fallback
        url_sources: list = [
            None,  # Auto-detect via Lavalink
            wavelink.TrackSource.YouTube,
            wavelink.TrackSource.YouTubeMusic,
            wavelink.TrackSource.SoundCloud,
        ]

        for src in url_sources:
            try:
                tracks = await wavelink.Playable.search(query, source=src)
                if tracks:
                    return tracks
            except Exception as exc:
                last_error = exc
                logger.warning("URL search failed via source=%s for %r: %s", src, query, exc)
                continue

        if last_error:
            raise last_error
        return []

    # Non-URL search - use configured source with fallbacks
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
