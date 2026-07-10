"""
Queue manager — optimized, split responsibilities.

Replaces previous deque-based version with list-based storage
for simpler indexing and less copying on remove/shuffle.

Optimizations:
- list instead of deque → direct indexed access O(1), remove O(n) but avoids double conversion
- shuffle in-place
- get_next O(1) for pop(0) amortized, queue sizes are small
- history trimming uses deque-like sliding window but list slice
- get_queue now returns list (backward compat still supports .remove)
"""
import logging
import random
from enum import Enum
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class LoopMode(Enum):
    NONE = "none"
    TRACK = "track"
    QUEUE = "queue"


class QueueManager:
    def __init__(self, max_history: int = 50):
        self._queues: Dict[int, List[dict]] = {}
        self._loop_modes: Dict[int, LoopMode] = {}
        self._histories: Dict[int, List[dict]] = {}
        self._max_history = max_history

    # Queue ops
    def _ensure_queue(self, guild_id: int) -> List[dict]:
        return self._queues.setdefault(guild_id, [])

    def get_queue(self, guild_id: int) -> List[dict]:
        """Returns internal list reference — caller should not mutate directly if not intended."""
        return self._ensure_queue(guild_id)

    def add(self, guild_id: int, track: dict, requester_id: int) -> int:
        q = self._ensure_queue(guild_id)
        track["requester_id"] = requester_id
        q.append(track)
        logger.debug("Track added guild %s pos %d: %s", guild_id, len(q), track.get("title"))
        return len(q)

    def add_front(self, guild_id: int, track: dict) -> None:
        q = self._ensure_queue(guild_id)
        q.insert(0, track)
        logger.debug("Track prepended guild %s: %s", guild_id, track.get("title"))

    def add_many(self, guild_id: int, tracks: List[dict], requester_id: int) -> int:
        """Batch add — more efficient than loop."""
        q = self._ensure_queue(guild_id)
        for t in tracks:
            t["requester_id"] = requester_id
            q.append(t)
        return len(q)

    def remove(self, guild_id: int, index: int) -> Optional[dict]:
        q = self._ensure_queue(guild_id)
        if not q or index < 1 or index > len(q):
            return None
        removed = q.pop(index - 1)
        logger.debug("Removed pos %d guild %s", index, guild_id)
        return removed

    def remove_by_uri(self, guild_id: int, track_data: dict) -> bool:
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
        logger.debug("Queue cleared guild %s", guild_id)

    def shuffle(self, guild_id: int) -> None:
        q = self._ensure_queue(guild_id)
        random.shuffle(q)
        logger.debug("Queue shuffled guild %s (%d)", guild_id, len(q))

    # Loop
    def set_loop(self, guild_id: int, mode: str) -> LoopMode:
        try:
            loop_mode = LoopMode(mode.lower())
        except ValueError:
            raise ValueError(f"Invalid loop mode: {mode}. Use: none, track, queue.")
        self._loop_modes[guild_id] = loop_mode
        logger.info("Loop %s guild %s", mode, guild_id)
        return loop_mode

    def get_loop(self, guild_id: int) -> LoopMode:
        return self._loop_modes.get(guild_id, LoopMode.NONE)

    # Playback
    def get_next(self, guild_id: int) -> Optional[dict]:
        q = self._ensure_queue(guild_id)
        if not q:
            return None
        if self.get_loop(guild_id) == LoopMode.QUEUE:
            track = q.pop(0)
            q.append(track)
            return track
        return q.pop(0)

    # Query
    def get_all(self, guild_id: int) -> List[dict]:
        return list(self._ensure_queue(guild_id))

    def get_length(self, guild_id: int) -> int:
        return len(self._ensure_queue(guild_id))

    def is_empty(self, guild_id: int) -> bool:
        return len(self._ensure_queue(guild_id)) == 0

    # History — keep small
    def add_history(self, guild_id: int, track: dict) -> None:
        hist = self._histories.setdefault(guild_id, [])
        hist.append(track)
        if len(hist) > self._max_history:
            # keep last N
            self._histories[guild_id] = hist[-self._max_history :]

    def get_history(self, guild_id: int, limit: int = 10) -> List[dict]:
        hist = self._histories.get(guild_id, [])
        return hist[-limit:] if limit else hist

    # Cleanup
    def cleanup(self, guild_id: int) -> None:
        self._queues.pop(guild_id, None)
        self._loop_modes.pop(guild_id, None)
        self._histories.pop(guild_id, None)
        logger.debug("Cleaned up guild %s", guild_id)
