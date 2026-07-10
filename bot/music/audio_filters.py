"""
Audio filters for Lavalink via Wavelink Filters.
Provides presets like Bassboost, Nightcore, Vaporwave, Pop, etc.
"""

from __future__ import annotations

import logging
from typing import Dict, Optional

import wavelink

logger = logging.getLogger(__name__)

# Human readable descriptions matching screenshot
FILTER_INFO: Dict[str, Dict[str, str]] = {
    "reset": {
        "label": "Reset Filters",
        "description": "Remove all audio filters",
        "emoji": "🔄",
    },
    "bassboost": {
        "label": "Bassboost",
        "description": "Enhance bass frequencies",
        "emoji": "🔊",
    },
    "nightcore": {
        "label": "Nightcore",
        "description": "Increase speed and pitch",
        "emoji": "🌙",
    },
    "vaporwave": {
        "label": "Vaporwave",
        "description": "Slow down and lower pitch",
        "emoji": "🌊",
    },
    "pop": {
        "label": "Pop",
        "description": "Optimize for pop music",
        "emoji": "🎤",
    },
    "8d": {
        "label": "8D",
        "description": "Immersive 8D audio effect",
        "emoji": "🎧",
    },
    "karaoke": {
        "label": "Karaoke",
        "description": "Remove vocals for karaoke",
        "emoji": "🎙️",
    },
    "tremolo": {
        "label": "Tremolo",
        "description": "Shuddering volume effect",
        "emoji": "〰️",
    },
    "lofi": {
        "label": "Lo-Fi",
        "description": "Lo-fi chill effect",
        "emoji": "📻",
    },
}

VALID_FILTERS = set(FILTER_INFO.keys())


def _equalizer_bands(gains: list[float]) -> list[dict]:
    """Convert 0-14 gain list to Lavalink equalizer payload."""
    bands = []
    for i, g in enumerate(gains):
        if i > 14:
            break
        bands.append({"band": i, "gain": float(g)})
    # Ensure 15 bands total: pad with 0
    while len(bands) < 15:
        bands.append({"band": len(bands), "gain": 0.0})
    return bands


def build_filter(filter_name: str) -> Optional[wavelink.Filters]:
    """Build wavelink.Filters for given preset. None for reset."""
    name = filter_name.lower().strip()

    if name in ("reset", "clear", "off", "none"):
        # Empty filters = reset
        return wavelink.Filters()

    filters = wavelink.Filters()

    if name == "bassboost":
        # Boost low frequencies (bands 0-3)
        gains = [0.3, 0.25, 0.15, 0.1, 0.05, 0.0, -0.05, -0.05, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
        filters.equalizer.set(bands=_equalizer_bands(gains))
        # Alternative: low_pass might help but keep simple
        return filters

    if name == "nightcore":
        # Speed up + higher pitch
        filters.timescale.set(speed=1.25, pitch=1.3, rate=1.0)
        return filters

    if name == "vaporwave":
        filters.timescale.set(speed=0.8, pitch=0.8, rate=1.0)
        return filters

    if name == "pop":
        # Pop optimized EQ: slight boost in vocal ranges
        gains = [-0.05, 0.02, 0.08, 0.12, 0.10, 0.05, 0.02, -0.02, -0.02, 0.02, 0.05, 0.08, 0.10, 0.08, 0.05]
        filters.equalizer.set(bands=_equalizer_bands(gains))
        return filters

    if name == "8d":
        # 8D effect via rotation
        filters.rotation.set(rotation_hz=0.2)
        return filters

    if name == "karaoke":
        filters.karaoke.set(level=1.0, mono_level=1.0, filter_band=220.0, filter_width=100.0)
        return filters

    if name == "tremolo":
        filters.tremolo.set(frequency=2.0, depth=0.5)
        return filters

    if name == "lofi":
        # Lo-fi: low-pass + slight distortion + slow
        filters.low_pass.set(smoothing=20.0)
        filters.timescale.set(speed=0.9, pitch=0.9, rate=1.0)
        gains = [0.1, 0.1, 0.05, 0.0, -0.05, -0.05, -0.05, -0.05, -0.05, -0.05, 0.0, 0.0, 0.0, 0.0, 0.0]
        filters.equalizer.set(bands=_equalizer_bands(gains))
        return filters

    # Unknown
    return None


def get_filter_choices() -> list[tuple[str, str, str, str]]:
    """Return list of (value, label, description, emoji) for select menus, excluding extra."""
    # Core 5 like screenshot + extras
    order = ["reset", "bassboost", "nightcore", "vaporwave", "pop", "8d", "lofi", "karaoke", "tremolo"]
    choices = []
    for key in order:
        if key in FILTER_INFO:
            info = FILTER_INFO[key]
            choices.append((key, info["label"], info["description"], info["emoji"]))
    return choices


async def apply_filter_to_player(player, filter_name: str) -> str:
    """Apply filter to wavelink Player and track active filter name.

    Returns:
        Applied filter name (normalized).
    """
    normalized = filter_name.lower().strip()
    if normalized not in VALID_FILTERS:
        raise ValueError(f"Unknown filter: {filter_name}. Valid: {', '.join(VALID_FILTERS)}")

    filters_obj = build_filter(normalized)
    if filters_obj is None:
        # Should not happen for valid filters
        filters_obj = wavelink.Filters()

    # Apply via wavelink
    try:
        await player.set_filters(filters_obj)
    except Exception as e:
        logger.error("Failed to set filter %s: %s", normalized, e)
        raise

    # Track active filter on player for embed display
    try:
        setattr(player, "active_filter", normalized if normalized != "reset" else "off")
    except Exception:
        pass

    logger.info("Applied filter %s to guild %s", normalized, getattr(player, "guild", None))
    return normalized
