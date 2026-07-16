"""
Shared playback actions — refactored to use core services.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

import discord

from bot.core.services.auth import check_authorized_sync_from_bot
from bot.core.services.voice import get_player, voice_check
from bot.database import favorites_manager, guild_settings
from bot.music.audio_filters import FILTER_INFO, VALID_FILTERS
from bot.music.emoji import EMOJI
from bot.music.queue_manager import LoopMode

logger = logging.getLogger(__name__)


@dataclass
class ActionResult:
    ok: bool
    message: str
    ephemeral: bool = True
    refresh_player: bool = True


class PlayerController:
    """Centralized music control used by commands, buttons and dashboard."""

    def __init__(self, bot):
        self.bot = bot

    async def _broadcast(self, guild_id: int) -> None:
        """Broadcast player state update via WebSocket."""
        try:
            from bot.music.lavalink.events import _broadcast_player_update

            await _broadcast_player_update(self.bot, guild_id)
        except Exception as e:
            logger.debug("WS broadcast from controller failed: %s", e)

    # Helpers — now delegate to services
    def check_authorized(self, user_id: int) -> tuple[bool, str]:
        return check_authorized_sync_from_bot(self.bot, user_id)

    def is_owner(self, user_id: int) -> bool:
        return user_id == self.bot.config.owner_id

    def get_player(self, guild_id: int):
        return get_player(self.bot, guild_id)

    def _require_same_voice(
        self, member: discord.Member, player, *, soft: bool = False
    ) -> str | None:
        if soft:
            return None
        return voice_check(member, player)

    # Internal guard
    def _auth_or_fail(self, user_id: int) -> ActionResult | None:
        ok, err = self.check_authorized(user_id)
        if not ok:
            return ActionResult(False, err)
        return None

    def _voice_or_fail(self, member: discord.Member, player) -> ActionResult | None:
        err = self._require_same_voice(member, player)
        if err:
            return ActionResult(False, err)
        return None

    # Actions — each < 25 lines
    async def pause(self, guild_id: int, user: discord.Member) -> ActionResult:
        if res := self._auth_or_fail(user.id):
            return res
        player = self.get_player(guild_id)
        if not player or not player.playing:
            return ActionResult(False, f"{EMOJI['error']} Nothing is currently playing.")
        if res := self._voice_or_fail(user, player):
            return res
        if player.paused:
            return ActionResult(False, f"{EMOJI['error']} Already paused.", refresh_player=False)
        await player.pause(True)
        return ActionResult(True, f"{EMOJI['pause']} Paused.")

    async def resume(self, guild_id: int, user: discord.Member) -> ActionResult:
        if res := self._auth_or_fail(user.id):
            return res
        player = self.get_player(guild_id)
        if not player:
            return ActionResult(False, f"{EMOJI['error']} No active music session.")
        if res := self._voice_or_fail(user, player):
            return res
        if not player.paused:
            return ActionResult(
                False, f"{EMOJI['error']} Playback is not paused.", refresh_player=False
            )
        await player.pause(False)
        return ActionResult(True, f"{EMOJI['resume']} Resumed.")

    async def play_pause(self, guild_id: int, user: discord.Member) -> ActionResult:
        player = self.get_player(guild_id)
        if player and player.paused:
            return await self.resume(guild_id, user)
        return await self.pause(guild_id, user)

    async def skip(self, guild_id: int, user: discord.Member) -> ActionResult:
        if res := self._auth_or_fail(user.id):
            return res
        player = self.get_player(guild_id)
        if not player or not player.playing:
            return ActionResult(False, f"{EMOJI['error']} Nothing is currently playing.")
        if res := self._voice_or_fail(user, player):
            return res
        title = player.last_track.title if player.last_track else "Unknown"
        await player.stop()
        return ActionResult(True, f"{EMOJI['skip']} Skipped **{title}**.")

    async def stop(self, guild_id: int, user: discord.Member) -> ActionResult:
        if res := self._auth_or_fail(user.id):
            return res
        player = self.get_player(guild_id)
        if not player:
            return ActionResult(False, f"{EMOJI['error']} No active music session.")
        if res := self._voice_or_fail(user, player):
            return res
        await player.stop()
        self.bot.queue_manager.clear(guild_id)
        await self._broadcast(guild_id)
        return ActionResult(True, f"{EMOJI['stop']} Stopped and cleared queue.")

    async def shuffle(self, guild_id: int, user: discord.Member) -> ActionResult:
        if res := self._auth_or_fail(user.id):
            return res
        player = self.get_player(guild_id)
        if player and (err := self._require_same_voice(user, player)):
            return ActionResult(False, err)
        if self.bot.queue_manager.is_empty(guild_id):
            return ActionResult(False, f"{EMOJI['error']} The queue is empty.")
        self.bot.queue_manager.shuffle(guild_id)
        await self._broadcast(guild_id)
        return ActionResult(True, f"{EMOJI['shuffle']} Queue shuffled.")

    async def cycle_loop(self, guild_id: int, user: discord.Member) -> ActionResult:
        if res := self._auth_or_fail(user.id):
            return res
        player = self.get_player(guild_id)
        if player and (err := self._require_same_voice(user, player)):
            return ActionResult(False, err)
        current = self.bot.queue_manager.get_loop(guild_id)
        order = [LoopMode.NONE, LoopMode.TRACK, LoopMode.QUEUE]
        idx = order.index(current) if current in order else 0
        nxt = order[(idx + 1) % len(order)]
        self.bot.queue_manager.set_loop(guild_id, nxt.value)
        icons = {
            LoopMode.NONE: EMOJI["loop_none"],
            LoopMode.TRACK: EMOJI["loop_track"],
            LoopMode.QUEUE: EMOJI["loop_queue"],
        }
        return ActionResult(True, f"{icons[nxt]} Loop mode: **{nxt.value}**.")

    async def volume_delta(self, guild_id: int, user: discord.Member, delta: int) -> ActionResult:
        if res := self._auth_or_fail(user.id):
            return res
        player = self.get_player(guild_id)
        if not player:
            return ActionResult(False, f"{EMOJI['error']} No active music session.")
        if res := self._voice_or_fail(user, player):
            return res
        current = player.get_volume() if hasattr(player, "get_volume") else 50
        new_vol = max(0, min(100, current + delta))
        await player.set_volume(new_vol)
        try:
            guild_settings.set(str(guild_id), self.bot.config.database_path, volume=new_vol)
        except Exception as e:
            logger.debug("Failed to persist volume: %s", e)
        icon = EMOJI["vol_down"] if delta < 0 else EMOJI["vol_up"]
        return ActionResult(True, f"{icon} Volume: **{new_vol}%**.")

    async def set_volume(self, guild_id: int, user: discord.Member, volume: int) -> ActionResult:
        if res := self._auth_or_fail(user.id):
            return res
        player = self.get_player(guild_id)
        if not player:
            return ActionResult(False, f"{EMOJI['error']} No active music session.")
        if res := self._voice_or_fail(user, player):
            return res
        volume = max(0, min(100, volume))
        await player.set_volume(volume)
        try:
            guild_settings.set(str(guild_id), self.bot.config.database_path, volume=volume)
        except Exception as e:
            logger.debug("Failed to persist volume: %s", e)
        return ActionResult(True, f"{EMOJI['volume']} Volume set to **{volume}%**.")

    async def favorite(self, guild_id: int, user: discord.Member) -> ActionResult:
        if res := self._auth_or_fail(user.id):
            return res
        player = self.get_player(guild_id)
        if not player or not player.playing or not player.last_track:
            return ActionResult(False, f"{EMOJI['error']} Nothing is currently playing.")
        track = player.last_track
        success = favorites_manager.add_favorite(
            user_id=str(user.id),
            title=track.title,
            author=track.author,
            uri=track.uri,
            identifier=track.identifier,
            length=track.length,
            artwork_url=getattr(track, "artwork_url", None),
            db_path=self.bot.config.database_path,
        )
        if success:
            return ActionResult(
                True,
                f"{EMOJI['favorite']} Added **{track.title}** to your favorites.",
                refresh_player=False,
            )
        return ActionResult(
            False,
            f"{EMOJI['error']} **{track.title}** is already in your favorites.",
            refresh_player=False,
        )

    async def disconnect(self, guild_id: int, user: discord.Member) -> ActionResult:
        if res := self._auth_or_fail(user.id):
            return res
        player = self.get_player(guild_id)
        if not player:
            return ActionResult(False, f"{EMOJI['error']} Bot is not connected.")
        if res := self._voice_or_fail(user, player):
            return res
        self.bot.queue_manager.cleanup(guild_id)
        await player.disconnect()
        mgr = getattr(self.bot, "player_messages", None)
        if mgr:
            await mgr.set_idle(guild_id)
        return ActionResult(True, f"{EMOJI['disconnect']} Disconnected.", refresh_player=False)

    # Filters
    async def set_filter(
        self, guild_id: int, user: discord.Member, filter_name: str
    ) -> ActionResult:
        if res := self._auth_or_fail(user.id):
            return res
        player = self.get_player(guild_id)
        if not player or not player.playing:
            return ActionResult(False, f"{EMOJI['error']} Nothing is currently playing.")
        if res := self._voice_or_fail(user, player):
            return res
        normalized = filter_name.lower().strip()
        if normalized not in VALID_FILTERS:
            valid = ", ".join(sorted(VALID_FILTERS))
            return ActionResult(
                False, f"{EMOJI['error']} Unknown filter. Valid: `{valid}`", refresh_player=False
            )
        try:
            await player.set_audio_filter(normalized)
        except ValueError as ve:
            return ActionResult(False, f"{EMOJI['error']} {ve}", refresh_player=False)
        except Exception as e:
            logger.exception("Failed to apply filter %s", normalized)
            return ActionResult(
                False, f"{EMOJI['error']} Failed to apply filter: {e}", refresh_player=False
            )
        info = FILTER_INFO.get(normalized, {})
        label = info.get("label", normalized)
        emoji = info.get("emoji", "🎛️")
        if normalized in ("reset", "off"):
            return ActionResult(True, f"{emoji} Filters cleared — back to normal audio.")
        return ActionResult(True, f"{emoji} Filter applied: **{label}**.")

    async def get_filter(self, guild_id: int) -> str:
        player = self.get_player(guild_id)
        if not player:
            return "off"
        return getattr(player, "active_filter", "off")

    # Seeking
    async def seek_forward(
        self, guild_id: int, user: discord.Member, seconds: int = 10
    ) -> ActionResult:
        if res := self._auth_or_fail(user.id):
            return res
        player = self.get_player(guild_id)
        if not player or not player.playing:
            return ActionResult(False, f"{EMOJI['error']} Nothing is currently playing.")
        if res := self._voice_or_fail(user, player):
            return res
        try:
            new_pos = await player.seek_forward(seconds * 1000)
            from bot.music.embed_manager import EmbedManager

            pos_str = EmbedManager._format_duration(new_pos)
            return ActionResult(True, f"⏩ Seeked +{seconds}s → `{pos_str}`.")
        except Exception as e:
            return ActionResult(False, f"{EMOJI['error']} Seek failed: {e}")

    async def seek_backward(
        self, guild_id: int, user: discord.Member, seconds: int = 10
    ) -> ActionResult:
        if res := self._auth_or_fail(user.id):
            return res
        player = self.get_player(guild_id)
        if not player or not player.playing:
            return ActionResult(False, f"{EMOJI['error']} Nothing is currently playing.")
        if res := self._voice_or_fail(user, player):
            return res
        try:
            new_pos = await player.seek_backward(seconds * 1000)
            from bot.music.embed_manager import EmbedManager

            pos_str = EmbedManager._format_duration(new_pos)
            return ActionResult(True, f"⏪ Seeked -{seconds}s → `{pos_str}`.")
        except Exception as e:
            return ActionResult(False, f"{EMOJI['error']} Seek failed: {e}")

    async def replay(self, guild_id: int, user: discord.Member) -> ActionResult:
        if res := self._auth_or_fail(user.id):
            return res
        player = self.get_player(guild_id)
        if not player or not player.playing:
            return ActionResult(False, f"{EMOJI['error']} Nothing is currently playing.")
        if res := self._voice_or_fail(user, player):
            return res
        try:
            await player.replay()
            return ActionResult(True, "⏮️ Replaying current track.")
        except Exception as e:
            return ActionResult(False, f"{EMOJI['error']} Replay failed: {e}")
