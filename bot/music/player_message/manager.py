"""Main manager — orchestrates persistence + state + discord messages."""

from __future__ import annotations

import asyncio
import contextlib
import logging

import discord

from .persistence import PlayerPersistence
from .state import PlayerStateBuilder

logger = logging.getLogger(__name__)

PROGRESS_INTERVAL = 12


class PlayerMessageManager:
    def __init__(self, bot):
        self.bot = bot
        self._messages: dict[int, discord.Message] = {}
        self._tasks: dict[int, asyncio.Task] = {}
        self._persistence = PlayerPersistence(bot)
        self._state_builder = PlayerStateBuilder(bot)

    # Delegated helpers for backwards compat
    def _db_key(self, guild_id: int, kind: str) -> str:
        return self._persistence._db_key(guild_id, kind)

    def _save_ids(self, guild_id: int, channel_id: int, message_id: int) -> None:
        return self._persistence.save_ids(guild_id, channel_id, message_id)

    def _load_ids(self, guild_id: int):
        return self._persistence.load_ids(guild_id)

    def _clear_ids(self, guild_id: int) -> None:
        return self._persistence.clear_ids(guild_id)

    def _get_channel(self, guild_id: int):
        return self._state_builder.get_channel(guild_id)

    def _build_view(self, guild_id: int):
        return self._state_builder.build_view(guild_id)

    def _player_state(self, guild_id: int) -> dict:
        return self._state_builder.player_state(guild_id)

    def build_embed(self, guild_id: int) -> discord.Embed:
        return self._state_builder.build_embed(guild_id)

    async def ensure_message(
        self, guild_id: int, channel: discord.abc.Messageable | None = None
    ) -> discord.Message | None:
        if guild_id in self._messages:
            try:
                await self._messages[guild_id].channel.fetch_message(self._messages[guild_id].id)
                return self._messages[guild_id]
            except (discord.NotFound, discord.HTTPException, AttributeError):
                self._messages.pop(guild_id, None)

        channel_id, message_id = self._persistence.load_ids(guild_id)
        if channel_id and message_id:
            ch = self.bot.get_channel(channel_id)
            if ch is None:
                try:
                    ch = await self.bot.fetch_channel(channel_id)
                except Exception:
                    ch = None
            if ch is not None:
                try:
                    msg = await ch.fetch_message(message_id)
                    self._messages[guild_id] = msg
                    return msg
                except (discord.NotFound, discord.HTTPException):
                    self._persistence.clear_ids(guild_id)

        target = channel or self._state_builder.get_channel(guild_id)
        if target is None:
            logger.warning("No channel to post player message for guild %s", guild_id)
            return None

        embed = self._state_builder.build_embed(guild_id)
        view = self._state_builder.build_view(guild_id)
        try:
            msg = await target.send(embed=embed, view=view)
            self._messages[guild_id] = msg
            self._persistence.save_ids(guild_id, msg.channel.id, msg.id)
            with contextlib.suppress(Exception):
                self.bot.add_view(view, message_id=msg.id)
            logger.info("Created player message %s in guild %s", msg.id, guild_id)
            return msg
        except Exception as e:
            logger.error("Failed to create player message: %s", e)
            return None

    async def update_now_playing(self, guild_id: int) -> None:
        msg = await self.ensure_message(guild_id)
        if not msg:
            return
        embed = self._state_builder.build_embed(guild_id)
        view = self._state_builder.build_view(guild_id)
        try:
            await msg.edit(embed=embed, view=view)
            self._messages[guild_id] = msg
        except discord.NotFound:
            self._messages.pop(guild_id, None)
            self._persistence.clear_ids(guild_id)
            await self.ensure_message(guild_id)
        except discord.HTTPException as e:
            logger.debug("Player message edit failed: %s", e)

        state = self._state_builder.player_state(guild_id)
        if state["playing"] and not state["paused"]:
            self.start_progress_task(guild_id)
        else:
            self.stop_progress_task(guild_id)

    async def set_idle(self, guild_id: int) -> None:
        self.stop_progress_task(guild_id)
        await self.update_now_playing(guild_id)

    def start_progress_task(self, guild_id: int) -> None:
        if guild_id in self._tasks and not self._tasks[guild_id].done():
            return
        self._tasks[guild_id] = asyncio.create_task(self._progress_loop(guild_id))

    def stop_progress_task(self, guild_id: int) -> None:
        task = self._tasks.pop(guild_id, None)
        if task and not task.done():
            task.cancel()

    async def _progress_loop(self, guild_id: int) -> None:
        try:
            while True:
                await asyncio.sleep(PROGRESS_INTERVAL)
                state = self._state_builder.player_state(guild_id)
                if not state["playing"] or state["paused"]:
                    break
                msg = self._messages.get(guild_id)
                if not msg:
                    break
                embed = self._state_builder.build_embed(guild_id)
                try:
                    await msg.edit(embed=embed)
                except (discord.NotFound, discord.HTTPException):
                    break
        except asyncio.CancelledError:
            return
        except Exception as e:
            logger.debug("Progress loop ended: %s", e)
        finally:
            self._tasks.pop(guild_id, None)

    async def restore_views(self) -> None:
        guild_id = getattr(self.bot.config, "guild_id", None)
        if not guild_id:
            return
        channel_id, message_id = self._persistence.load_ids(guild_id)
        if not channel_id or not message_id:
            return
        try:
            ch = self.bot.get_channel(channel_id) or await self.bot.fetch_channel(channel_id)
            msg = await ch.fetch_message(message_id)
            view = self._state_builder.build_view(guild_id)
            self.bot.add_view(view, message_id=message_id)
            self._messages[guild_id] = msg
            await msg.edit(embed=self._state_builder.build_embed(guild_id), view=view)
            logger.info("Restored player view for guild %s message %s", guild_id, message_id)
            state = self._state_builder.player_state(guild_id)
            if state["playing"] and not state["paused"]:
                self.start_progress_task(guild_id)
        except Exception as e:
            logger.warning("Could not restore player message: %s", e)
