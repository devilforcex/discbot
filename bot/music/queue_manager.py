"""
Queue manager for the Discord Music Bot.
Manages per-guild song queues with loop, shuffle, and autoplay functionality.
"""

import logging
import random
from collections import deque
from enum import Enum
from typing import Optional

logger = logging.getLogger(__name__)


class LoopMode(Enum):
    """Loop mode for playback."""
    NONE = "none"
    TRACK = "track"
    QUEUE = "queue"


class QueueManager:
    """Manages music queues for multiple guilds.

    Maintains a separate queue, loop mode, and playback history per guild.
    """

    def __init__(self):
        self._queues: dict[int, deque] = {}
        self._loop_modes: dict[int, LoopMode] = {}
        self._histories: dict[int, list[dict]] = {}
        self._max_history: int = 50

    # --- Queue Operations ---

    def get_queue(self, guild_id: int) -> deque:
        """Get or create a queue for a guild.

        Args:
            guild_id: Discord guild ID.

        Returns:
            The deque representing the guild's queue.
        """
        if guild_id not in self._queues:
            self._queues[guild_id] = deque()
        return self._queues[guild_id]

    def add(self, guild_id: int, track: dict, requester_id: int) -> int:
        """Add a track to the end of the guild's queue.

        Args:
            guild_id: Discord guild ID.
            track: Track information dict.
            requester_id: Discord user ID who requested the track.

        Returns:
            The position of the added track (1-indexed).
        """
        queue = self.get_queue(guild_id)
        track["requester_id"] = requester_id
        queue.append(track)
        logger.debug(
            "Track added to queue for guild %s: %s (position %d)",
            guild_id, track.get("title", "unknown"), len(queue),
        )
        return len(queue)

    def add_front(self, guild_id: int, track: dict) -> None:
        """Prepend a track to the front of the queue (for autoplay).

        Args:
            guild_id: Discord guild ID.
            track: Track information dict.
        """
        queue = self.get_queue(guild_id)
        queue.appendleft(track)
        logger.debug(
            "Track prepended to queue for guild %s: %s",
            guild_id, track.get("title", "unknown"),
        )

    def remove(self, guild_id: int, index: int) -> Optional[dict]:
        """Remove a track from the queue by 1-indexed position.

        Args:
            guild_id: Discord guild ID.
            index: 1-based position of the track to remove.

        Returns:
            The removed track dict, or None if index is invalid.
        """
        queue = self.get_queue(guild_id)
        if not queue or index < 1 or index > len(queue):
            return None

        # Convert to list for indexed removal, then back to deque
        items = list(queue)
        removed = items.pop(index - 1)
        self._queues[guild_id] = deque(items)
        logger.debug("Removed track at position %d from guild %s", index, guild_id)
        return removed

    def clear(self, guild_id: int) -> None:
        """Clear all tracks from the guild's queue.

        Args:
            guild_id: Discord guild ID.
        """
        if guild_id in self._queues:
            self._queues[guild_id].clear()
        logger.debug("Queue cleared for guild %s", guild_id)

    def shuffle(self, guild_id: int) -> None:
        """Randomly shuffle the guild's queue.

        Args:
            guild_id: Discord guild ID.
        """
        queue = self.get_queue(guild_id)
        items = list(queue)
        random.shuffle(items)
        self._queues[guild_id] = deque(items)
        logger.debug("Queue shuffled for guild %s (%d tracks)", guild_id, len(items))

    # --- Loop Mode ---

    def set_loop(self, guild_id: int, mode: str) -> LoopMode:
        """Set the loop mode for a guild.

        Args:
            guild_id: Discord guild ID.
            mode: One of 'none', 'track', 'queue'.

        Returns:
            The new LoopMode.

        Raises:
            ValueError: If mode is not a valid LoopMode.
        """
        try:
            loop_mode = LoopMode(mode.lower())
        except ValueError:
            raise ValueError(f"Invalid loop mode: {mode}. Use: none, track, queue.")

        self._loop_modes[guild_id] = loop_mode
        logger.info("Loop mode set to '%s' for guild %s", mode, guild_id)
        return loop_mode

    def get_loop(self, guild_id: int) -> LoopMode:
        """Get the current loop mode for a guild.

        Args:
            guild_id: Discord guild ID.

        Returns:
            The current LoopMode (defaults to NONE).
        """
        return self._loop_modes.get(guild_id, LoopMode.NONE)

    # --- Playback ---

    def get_next(self, guild_id: int) -> Optional[dict]:
        """Get the next track to play, respecting loop mode.

        For loop none: pops from queue.
        For loop track: returns the current track (caller must replay).
        For loop queue: pops and appends to end.

        Args:
            guild_id: Discord guild ID.

        Returns:
            The next track dict, or None if queue is empty.
        """
        queue = self.get_queue(guild_id)
        loop_mode = self.get_loop(guild_id)

        if loop_mode == LoopMode.QUEUE and queue:
            # Pop from front, append to back, return popped track
            track = queue.popleft()
            queue.append(track)
            return track

        # LoopMode.NONE or LoopMode.TRACK — just pop next
        return queue.popleft() if queue else None

    def get_repeating_track(self, guild_id: int) -> Optional[dict]:
        """Get the track to repeat (for loop track mode).

        This returns the last track that was played. The caller is responsible
        for storing and providing the last played track.

        Args:
            guild_id: Discord guild ID.

        Returns:
            None — caller should replay the stored current track.
        """
        return None

    # --- Query ---

    def get_all(self, guild_id: int) -> list[dict]:
        """Get all tracks in the guild's queue as a list.

        Args:
            guild_id: Discord guild ID.

        Returns:
            List of track dicts in queue order.
        """
        return list(self.get_queue(guild_id))

    def get_length(self, guild_id: int) -> int:
        """Get the number of tracks in the guild's queue.

        Args:
            guild_id: Discord guild ID.

        Returns:
            Queue length.
        """
        return len(self.get_queue(guild_id))

    def is_empty(self, guild_id: int) -> bool:
        """Check if the guild's queue is empty.

        Args:
            guild_id: Discord guild ID.

        Returns:
            True if queue is empty.
        """
        return len(self.get_queue(guild_id)) == 0

    # --- History ---

    def add_history(self, guild_id: int, track: dict) -> None:
        """Add a track to the playback history.

        Args:
            guild_id: Discord guild ID.
            track: The track that was played.
        """
        if guild_id not in self._histories:
            self._histories[guild_id] = []

        self._histories[guild_id].append(track)

        # Trim history
        if len(self._histories[guild_id]) > self._max_history:
            self._histories[guild_id] = self._histories[guild_id][-self._max_history:]

    def get_history(self, guild_id: int, limit: int = 10) -> list[dict]:
        """Get recent playback history for a guild.

        Args:
            guild_id: Discord guild ID.
            limit: Maximum number of entries to return.

        Returns:
            List of recent tracks.
        """
        history = self._histories.get(guild_id, [])
        return history[-limit:]

    # --- Cleanup ---

    def cleanup(self, guild_id: int) -> None:
        """Remove all state for a guild (queue, loop mode, history).

        Args:
            guild_id: Discord guild ID.
        """
        self._queues.pop(guild_id, None)
        self._loop_modes.pop(guild_id, None)
        self._histories.pop(guild_id, None)
        logger.debug("Cleaned up queue state for guild %s", guild_id)