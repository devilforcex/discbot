"""
Shared playback actions for commands, button views, and dashboard.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Optional

import discord
import wavelink

from bot.database import favorites_manager, guild_settings
from bot.database.database import get_connection
from bot.music.emoji import EMOJI
from bot.music.queue_manager import LoopMode

logger = logging.getLogger(__name__)


@dataclass
class ActionResult:
    """Result of a player control action."""

    ok: bool
    message: str
    ephemeral: bool = True
    refresh_player: bool = True


class PlayerController:
    """Centralized music control used by prefix commands and UI buttons."""

    def __init__(self, bot):
        self.bot = bot

    # ------------------------------------------------------------------
    # Auth helpers
    # ------------------------------------------------------------------

    def is_owner(self, user_id: int) -> bool:
        return user_id == self.bot.config.owner_id

    def check_authorized(self, user_id: int) -> tuple[bool, str]:
        """Return (allowed, error_message). Owner always allowed."""
        if self.is_owner(user_id):
            return True, ""

        uid = str(user_id)
        try:
            conn = get_connection(self.bot.config.database_path)
            cur = conn.cursor()
            cur.execute("SELECT 1 FROM blacklisted_users WHERE user_id = ?", (uid,))
            if cur.fetchone():
                return False, f"{EMOJI['error']} You are blacklisted."
            cur.execute("SELECT 1 FROM approved_users WHERE user_id = ?", (uid,))
            if cur.fetchone():
                return True, ""
        except Exception as e:
            logger.error("Auth check failed for %s: %s", uid, e)

        return False, f"{EMOJI['error']} You are not authorized to use this bot."

    def get_player(self, guild_id: int):
        return discord.utils.get(self.bot.voice_clients, guild__id=guild_id)

    def _require_same_voice(
        self,
        member: discord.Member,
        player,
        *,
        soft: bool = False,
    ) -> Optional[str]:
        """Return error message if voice check fails, else None."""
        if soft:
            return None
        if not member.voice or not member.voice.channel:
            return f"{EMOJI['error']} You must be in a voice channel."
        if player and player.channel and member.voice.channel != player.channel:
            return f"{EMOJI['error']} You must be in the same voice channel as the bot."
        return None

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------

    async def pause(self, guild_id: int, user: discord.Member) -> ActionResult:
        ok, err = self.check_authorized(user.id)
        if not ok:
            return ActionResult(False, err)

        player = self.get_player(guild_id)
        if not player or not player.playing:
            return ActionResult(False, f"{EMOJI['error']} Nothing is currently playing.")

        vc_err = self._require_same_voice(user, player)
        if vc_err:
            return ActionResult(False, vc_err)

        if player.paused:
            return ActionResult(False, f"{EMOJI['error']} Already paused.", refresh_player=False)

        await player.pause(True)
        return ActionResult(True, f"{EMOJI['pause']} Paused.")

    async def resume(self, guild_id: int, user: discord.Member) -> ActionResult:
        ok, err = self.check_authorized(user.id)
        if not ok:
            return ActionResult(False, err)

        player = self.get_player(guild_id)
        if not player:
            return ActionResult(False, f"{EMOJI['error']} No active music session.")

        vc_err = self._require_same_voice(user, player)
        if vc_err:
            return ActionResult(False, vc_err)

        if not player.paused:
            return ActionResult(False, f"{EMOJI['error']} Playback is not paused.", refresh_player=False)

        await player.pause(False)
        return ActionResult(True, f"{EMOJI['resume']} Resumed.")

    async def play_pause(self, guild_id: int, user: discord.Member) -> ActionResult:
        player = self.get_player(guild_id)
        if player and player.paused:
            return await self.resume(guild_id, user)
        return await self.pause(guild_id, user)

    async def skip(self, guild_id: int, user: discord.Member) -> ActionResult:
        ok, err = self.check_authorized(user.id)
        if not ok:
            return ActionResult(False, err)

        player = self.get_player(guild_id)
        if not player or not player.playing:
            return ActionResult(False, f"{EMOJI['error']} Nothing is currently playing.")

        vc_err = self._require_same_voice(user, player)
        if vc_err:
            return ActionResult(False, vc_err)

        title = player.last_track.title if player.last_track else "Unknown"
        await player.stop()
        return ActionResult(True, f"{EMOJI['skip']} Skipped **{title}**.")

    async def stop(self, guild_id: int, user: discord.Member) -> ActionResult:
        ok, err = self.check_authorized(user.id)
        if not ok:
            return ActionResult(False, err)

        player = self.get_player(guild_id)
        if not player:
            return ActionResult(False, f"{EMOJI['error']} No active music session.")

        vc_err = self._require_same_voice(user, player)
        if vc_err:
            return ActionResult(False, vc_err)

        await player.stop()
        self.bot.queue_manager.clear(guild_id)
        return ActionResult(True, f"{EMOJI['stop']} Stopped and cleared queue.")

    async def shuffle(self, guild_id: int, user: discord.Member) -> ActionResult:
        ok, err = self.check_authorized(user.id)
        if not ok:
            return ActionResult(False, err)

        player = self.get_player(guild_id)
        vc_err = self._require_same_voice(user, player) if player else None
        if vc_err:
            return ActionResult(False, vc_err)

        if self.bot.queue_manager.is_empty(guild_id):
            return ActionResult(False, f"{EMOJI['error']} The queue is empty.")

        self.bot.queue_manager.shuffle(guild_id)
        return ActionResult(True, f"{EMOJI['shuffle']} Queue shuffled.")

    async def cycle_loop(self, guild_id: int, user: discord.Member) -> ActionResult:
        ok, err = self.check_authorized(user.id)
        if not ok:
            return ActionResult(False, err)

        player = self.get_player(guild_id)
        vc_err = self._require_same_voice(user, player) if player else None
        if vc_err:
            return ActionResult(False, vc_err)

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
        return ActionResult(
            True,
            f"{icons[nxt]} Loop mode: **{nxt.value}**.",
        )

    async def volume_delta(
        self,
        guild_id: int,
        user: discord.Member,
        delta: int,
    ) -> ActionResult:
        ok, err = self.check_authorized(user.id)
        if not ok:
            return ActionResult(False, err)

        player = self.get_player(guild_id)
        if not player:
            return ActionResult(False, f"{EMOJI['error']} No active music session.")

        vc_err = self._require_same_voice(user, player)
        if vc_err:
            return ActionResult(False, vc_err)

        current = player.get_volume() if hasattr(player, "get_volume") else 50
        new_vol = max(0, min(100, current + delta))
        await player.set_volume(new_vol)
        try:
            guild_settings.set(str(guild_id), self.bot.config.database_path, volume=new_vol)
        except Exception as e:
            logger.debug("Failed to persist volume: %s", e)

        icon = EMOJI["vol_down"] if delta < 0 else EMOJI["vol_up"]
        return ActionResult(True, f"{icon} Volume: **{new_vol}%**.")

    async def set_volume(
        self,
        guild_id: int,
        user: discord.Member,
        volume: int,
    ) -> ActionResult:
        ok, err = self.check_authorized(user.id)
        if not ok:
            return ActionResult(False, err)

        player = self.get_player(guild_id)
        if not player:
            return ActionResult(False, f"{EMOJI['error']} No active music session.")

        vc_err = self._require_same_voice(user, player)
        if vc_err:
            return ActionResult(False, vc_err)

        volume = max(0, min(100, volume))
        await player.set_volume(volume)
        try:
            guild_settings.set(str(guild_id), self.bot.config.database_path, volume=volume)
        except Exception as e:
            logger.debug("Failed to persist volume: %s", e)

        return ActionResult(True, f"{EMOJI['volume']} Volume set to **{volume}%**.")

    async def favorite(self, guild_id: int, user: discord.Member) -> ActionResult:
        ok, err = self.check_authorized(user.id)
        if not ok:
            return ActionResult(False, err)

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
        ok, err = self.check_authorized(user.id)
        if not ok:
            return ActionResult(False, err)

        player = self.get_player(guild_id)
        if not player:
            return ActionResult(False, f"{EMOJI['error']} Bot is not connected.")

        vc_err = self._require_same_voice(user, player)
        if vc_err:
            return ActionResult(False, vc_err)

        self.bot.queue_manager.cleanup(guild_id)
        await player.disconnect()

        # Idle player message
        mgr = getattr(self.bot, "player_messages", None)
        if mgr:
            await mgr.set_idle(guild_id)

        return ActionResult(
            True,
            f"{EMOJI['disconnect']} Disconnected.",
            refresh_player=False,
        )
