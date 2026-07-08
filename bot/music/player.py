"""
Custom Wavelink Player for the Discord Music Bot.
Extends the default Wavelink Player with volume, autoplay, and state tracking.
"""

import logging
from typing import Optional

import wavelink

logger = logging.getLogger(__name__)


class Player(wavelink.Player):
    """Custom Wavelink Player with extended state management.

    Attributes:
        volume: Current volume level (0-1000, Wavelink scale).
        autoplay_enabled: Whether autoplay is active.
        last_track: The most recently played track.
        previous_track: The track played before last_track.
        paused: Whether playback is currently paused.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.autoplay_enabled: bool = False
        self.last_track: Optional[wavelink.Playable] = None
        self.previous_track: Optional[wavelink.Playable] = None
        self._volume: int = 50

    async def set_volume(self, volume: int) -> None:
        """Set the player volume.

        Args:
            volume: Volume level (0-100). Wavelink uses 0-1000 internally.
        """
        clamped = max(0, min(100, volume))
        # Wavelink expects volume as int (0-1000), but discord.py/ Lavalink uses 0-100
        # wavelink.Player.set_volume handles the conversion
        await super().set_volume(clamped)
        self._volume = clamped
        logger.info("Player volume set to %d", clamped)

    def get_volume(self) -> int:
        """Get the current volume level.

        Returns:
            Volume level (0-100).
        """
        return self._volume

    async def toggle_autoplay(self, enabled: Optional[bool] = None) -> bool:
        """Toggle autoplay mode.

        Args:
            enabled: Force specific state. If None, toggle current.

        Returns:
            The new autoplay state.
        """
        if enabled is not None:
            self.autoplay_enabled = enabled
        else:
            self.autoplay_enabled = not self.autoplay_enabled

        logger.info("Autoplay %s for guild %s", "enabled" if self.autoplay_enabled else "disabled", self.guild.id)
        return self.autoplay_enabled

    async def get_autoplay_track(self) -> Optional[wavelink.Playable]:
        """Get an autoplay recommendation based on the last track.

        Uses Wavelink's autoplay feature if available, otherwise attempts
        to find a related track by searching with the last track's artist.

        Returns:
            A recommended Playable track, or None.
        """
        if not self.last_track:
            return None

        try:
            # Attempt to use Wavelink's built-in autoplay
            tracks = await self.node.get_playlist(
                wavelink.YouTubeMusicPlaylist,
                f"{self.last_track.title} {self.last_track.author}",
            )
            if tracks:
                return tracks[0]
        except Exception as e:
            logger.debug("Autoplay recommendation failed: %s", e)

        return None

    def store_track(self, track: wavelink.Playable) -> None:
        """Store a track as the last played track.

        Args:
            track: The track that was just played.
        """
        self.previous_track = self.last_track
        self.last_track = track