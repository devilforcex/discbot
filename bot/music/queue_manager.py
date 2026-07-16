"""
Queue manager — optimized, split responsibilities.

Stores wavelink.Playable objects directly for O(1) track retrieval.
Converts to dict only when needed for embeds/history.
"""

import contextlib
import logging
import random
from enum import Enum
from typing import TYPE_CHECKING, Optional

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from bot.music.player import Player


class LoopMode(Enum):
    NONE = "none"
    TRACK = "track"
    QUEUE = "queue"


# Max queue size to prevent memory exhaustion / abuse
MAX_QUEUE_SIZE = 500


class QueueManager:
    def __init__(self, max_history: int = 50):
        self._queues: dict[int, list[Player]] = {}  # stores Playable (wavelink.Playable)
        self._loop_modes: dict[int, LoopMode] = {}
        self._histories: dict[int, list[dict]] = {}  # history stores dicts for DB serialization
        self._max_history = max_history
        # For QUEUE loop mode: index instead of pop/append to avoid O(n) shift
        self._queue_indices: dict[int, int] = {}

    # Queue ops
    def _ensure_queue(self, guild_id: int) -> list["Player"]:
        return self._queues.setdefault(guild_id, [])

    def get_queue(self, guild_id: int) -> list["Player"]:
        """Returns internal list reference — caller should not mutate directly if not intended."""
        return self._ensure_queue(guild_id)

    def add(self, guild_id: int, track: "Player", requester_id: int) -> int:
        q = self._ensure_queue(guild_id)
        if len(q) >= MAX_QUEUE_SIZE:
            raise ValueError(f"Queue is full (max {MAX_QUEUE_SIZE} tracks).")
        # Store requester_id on the track object for embeds
        with contextlib.suppress(Exception):
            track.requester_id = requester_id
        q.append(track)
        logger.debug(
            "Track added guild %s pos %d: %s", guild_id, len(q), getattr(track, "title", "?")
        )
        return len(q)

    def add_front(self, guild_id: int, track: "Player") -> None:
        q = self._ensure_queue(guild_id)
        if len(q) >= MAX_QUEUE_SIZE:
            raise ValueError(f"Queue is full (max {MAX_QUEUE_SIZE} tracks).")
        with contextlib.suppress(Exception):
            track.requester_id = 0
        q.insert(0, track)
        logger.debug("Track prepended guild %s: %s", guild_id, getattr(track, "title", "?"))

    def add_many(self, guild_id: int, tracks: list["Player"], requester_id: int) -> int:
        """Batch add — more efficient than loop."""
        q = self._ensure_queue(guild_id)
        if len(q) + len(tracks) > MAX_QUEUE_SIZE:
            raise ValueError(f"Queue would exceed max size {MAX_QUEUE_SIZE}.")
        for t in tracks:
            with contextlib.suppress(Exception):
                t.requester_id = requester_id
            q.append(t)
        return len(q)

    def remove(self, guild_id: int, index: int) -> Optional["Player"]:
        q = self._ensure_queue(guild_id)
        if not q or index < 1 or index > len(q):
            return None
        removed = q.pop(index - 1)
        logger.debug("Removed pos %d guild %s", index, guild_id)
        return removed

    def remove_by_uri(self, guild_id: int, track_data: "Player") -> bool:
        """Used by lavalink client to discard bad tracks."""
        q = self._ensure_queue(guild_id)
        try:
            q.remove(track_data)
            return True
        except ValueError:
            return False

    def clear(self, guild_id: int) -> None:
        if guild_id in self._queues:
            self._queues[guild_id].clear()
        self._queue_indices.pop(guild_id, None)
        logger.debug("Queue cleared guild %s", guild_id)

    def shuffle(self, guild_id: int) -> None:
        q = self._ensure_queue(guild_id)
        random.shuffle(q)
        self._queue_indices.pop(guild_id, None)
        logger.debug("Queue shuffled guild %s (%d)", guild_id, len(q))

    # Loop
    def set_loop(self, guild_id: int, mode: str) -> LoopMode:
        try:
            loop_mode = LoopMode(mode.lower())
        except ValueError:
            raise ValueError(f"Invalid loop mode: {mode}. Use: none, track, queue.") from None
        self._loop_modes[guild_id] = loop_mode
        if loop_mode == LoopMode.QUEUE:
            self._queue_indices[guild_id] = 0
        else:
            self._queue_indices.pop(guild_id, None)
        logger.info("Loop %s guild %s", mode, guild_id)
        return loop_mode

    def get_loop(self, guild_id: int) -> LoopMode:
        return self._loop_modes.get(guild_id, LoopMode.NONE)

    # Playback
    def get_next(self, guild_id: int) -> Optional["Player"]:
        q = self._ensure_queue(guild_id)
        if not q:
            return None
        loop_mode = self.get_loop(guild_id)
        if loop_mode == LoopMode.QUEUE:
            idx = self._queue_indices.get(guild_id, 0)
            track = q[idx]
            self._queue_indices[guild_id] = (idx + 1) % len(q)
            return track
        return q.pop(0)

    # Query — returns list of dicts for embeds
    def get_all_as_dicts(self, guild_id: int) -> list[dict]:
        """Convert queue to list of dicts for embed building."""
        q = self._ensure_queue(guild_id)
        return [self._track_to_dict(t) for t in q]

    def get_all(self, guild_id: int) -> list["Player"]:
        """Returns raw Playable objects (for iteration)."""
        return list(self._ensure_queue(guild_id))

    def get_length(self, guild_id: int) -> int:
        return len(self._ensure_queue(guild_id))

    def is_empty(self, guild_id: int) -> bool:
        return len(self._ensure_queue(guild_id)) == 0

    # History — keep small, stores dicts for DB
    def add_history(self, guild_id: int, track: "Player") -> None:
        hist = self._histories.setdefault(guild_id, [])
        hist.append(self._track_to_dict(track))
        if len(hist) > self._max_history:
            self._histories[guild_id] = hist[-self._max_history :]

    def get_history(self, guild_id: int, limit: int = 10) -> list[dict]:
        hist = self._histories.get(guild_id, [])
        return hist[-limit:] if limit else hist

    def _track_to_dict(self, track: "Player") -> dict:
        """Convert Playable to dict for embeds/history."""
        return {
            "title": getattr(track, "title", "Unknown"),
            "author": getattr(track, "author", "Unknown"),
            "uri": getattr(track, "uri", ""),
            "identifier": getattr(track, "identifier", ""),
            "length": getattr(track, "length", 0),
            "artwork_url": getattr(track, "artwork_url", None),
            "requester_id": getattr(track, "requester_id", 0),
        }

    # Cleanup
    def cleanup(self, guild_id: int) -> None:
        self._queues.pop(guild_id, None)
        self._loop_modes.pop(guild_id, None)
        self._histories.pop(guild_id, None)
        self._queue_indices.pop(guild_id, None)
        logger.debug("Cleaned up guild %s", guild_id)
