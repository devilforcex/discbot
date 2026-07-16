"""
Custom Wavelink Player for the Discord Music Bot.
Extends the default Wavelink Player with volume, autoplay, and state tracking.
"""

import logging

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
        self.last_track: wavelink.Playable | None = None
        self.previous_track: wavelink.Playable | None = None
        self._volume: int = 50
        self.active_filter: str = "off"  # reset / off = no filter
        self._last_position: int = 0

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

    async def toggle_autoplay(self, enabled: bool | None = None) -> bool:
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

        logger.info(
            "Autoplay %s for guild %s",
            "enabled" if self.autoplay_enabled else "disabled",
            self.guild.id,
        )
        return self.autoplay_enabled

    async def get_autoplay_track(self) -> wavelink.Playable | None:
        """Get an autoplay recommendation based on the last track.

        Uses Wavelink's autoplay feature if available, otherwise attempts
        to find a related track by searching with the last track's artist.
        Picks randomly from top results for variety.

        Returns:
            A recommended Playable track, or None.
        """
        import random

        if not self.last_track:
            return None

        # 1. Try Wavelink's built-in autoplay (YouTube Music playlist)
        try:
            tracks = await self.node.get_playlist(
                wavelink.YouTubeMusicPlaylist,
                f"{self.last_track.title} {self.last_track.author}",
            )
            if tracks:
                candidates = [
                    t
                    for t in tracks[:10]
                    if getattr(t, "uri", None) != getattr(self.last_track, "uri", None)
                ]
                if candidates:
                    logger.debug("Autoplay YTM playlist found %d candidates", len(candidates))
                    return random.choice(candidates)
        except Exception as e:
            logger.debug("Autoplay YTM playlist failed: %s", e)

        # 2. Fallback: YouTubeMusic search (lighter than playlist)
        try:
            search_query = f"{self.last_track.author} {self.last_track.title}"
            tracks = await wavelink.Playable.search(
                search_query,
                source=wavelink.TrackSource.YouTubeMusic,
            )
            candidates = [
                t
                for t in tracks[:10]
                if getattr(t, "uri", None) != getattr(self.last_track, "uri", None)
            ]
            if candidates:
                logger.debug("Autoplay YTM search found %d candidates", len(candidates))
                return random.choice(candidates)
        except Exception as e:
            logger.debug("Autoplay YTM search failed: %s", e)

        # 3. Fallback: search by artist only
        try:
            tracks = await wavelink.Playable.search(
                self.last_track.author,
                source=wavelink.TrackSource.YouTubeMusic,
            )
            candidates = [
                t
                for t in tracks[:10]
                if getattr(t, "uri", None) != getattr(self.last_track, "uri", None)
            ]
            if candidates:
                logger.debug("Autoplay artist search found %d candidates", len(candidates))
                return random.choice(candidates)
        except Exception as e:
            logger.debug("Autoplay artist search failed: %s", e)

        # 4. Final fallback: search by title + artist on YouTube
        try:
            search_query = f"{self.last_track.author} {self.last_track.title}"
            tracks = await wavelink.Playable.search(
                search_query,
                source=wavelink.TrackSource.YouTube,
            )
            candidates = [
                t
                for t in tracks[:10]
                if getattr(t, "uri", None) != getattr(self.last_track, "uri", None)
            ]
            if candidates:
                logger.debug("Autoplay YT search found %d candidates", len(candidates))
                return random.choice(candidates)
        except Exception as e:
            logger.debug("Autoplay YT search failed: %s", e)

        return None

    def store_track(self, track: wavelink.Playable) -> None:
        """Store a track as the last played track.

        Args:
            track: The track that was just played.
        """
        self.previous_track = self.last_track
        self.last_track = track

    async def set_audio_filter(self, filter_name: str) -> str:
        """Apply an audio filter via audio_filters module."""
        from bot.music.audio_filters import apply_filter_to_player

        applied = await apply_filter_to_player(self, filter_name)
        self.active_filter = applied if applied != "reset" else "off"
        return self.active_filter

    async def seek_forward(self, milliseconds: int = 10000) -> int:
        """Seek forward by ms, returns new position."""
        if not self.playing or not self.last_track:
            raise ValueError("Nothing is playing.")
        # position is property? In wavelink, self.position is current pos
        try:
            current = self.position
        except Exception:
            current = self._last_position
        new_pos = min(
            current + milliseconds,
            self.last_track.length - 500 if self.last_track.length else current + milliseconds,
        )
        await self.seek(new_pos)
        return new_pos

    async def seek_backward(self, milliseconds: int = 10000) -> int:
        if not self.playing or not self.last_track:
            raise ValueError("Nothing is playing.")
        try:
            current = self.position
        except Exception:
            current = self._last_position
        new_pos = max(0, current - milliseconds)
        await self.seek(new_pos)
        return new_pos

    async def replay(self) -> None:
        if not self.playing:
            raise ValueError("Nothing is playing.")
        await self.seek(0)
