"""
Persistent Now Playing message manager.
Keeps a single editable player embed + buttons per guild.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Optional

import discord

from bot.database.database import get_connection
from bot.music.embed_manager import EmbedManager
from bot.music.player_view import PlayerView

logger = logging.getLogger(__name__)

PROGRESS_INTERVAL = 12  # seconds between progress edits


class PlayerMessageManager:
    """Tracks and updates the guild's Now Playing message."""

    def __init__(self, bot):
        self.bot = bot
        # guild_id -> discord.Message
        self._messages: dict[int, discord.Message] = {}
        self._tasks: dict[int, asyncio.Task] = {}

    def _db_key(self, guild_id: int, kind: str) -> str:
        return f"player_{kind}_{guild_id}"

    def _save_ids(self, guild_id: int, channel_id: int, message_id: int) -> None:
        try:
            conn = get_connection(self.bot.config.database_path)
            cur = conn.cursor()
            for key, value in (
                (self._db_key(guild_id, "channel"), str(channel_id)),
                (self._db_key(guild_id, "message"), str(message_id)),
            ):
                cur.execute(
                    """
                    INSERT INTO bot_settings (key, value) VALUES (?, ?)
                    ON CONFLICT(key) DO UPDATE SET value = excluded.value
                    """,
                    (key, value),
                )
            conn.commit()
        except Exception as e:
            logger.debug("Failed to save player message ids: %s", e)

    def _load_ids(self, guild_id: int) -> tuple[Optional[int], Optional[int]]:
        try:
            conn = get_connection(self.bot.config.database_path)
            cur = conn.cursor()
            cur.execute(
                "SELECT value FROM bot_settings WHERE key = ?",
                (self._db_key(guild_id, "channel"),),
            )
            ch = cur.fetchone()
            cur.execute(
                "SELECT value FROM bot_settings WHERE key = ?",
                (self._db_key(guild_id, "message"),),
            )
            msg = cur.fetchone()
            channel_id = int(ch["value"]) if ch and ch["value"] else None
            message_id = int(msg["value"]) if msg and msg["value"] else None
            return channel_id, message_id
        except Exception as e:
            logger.debug("Failed to load player message ids: %s", e)
            return None, None

    def _clear_ids(self, guild_id: int) -> None:
        try:
            conn = get_connection(self.bot.config.database_path)
            cur = conn.cursor()
            cur.execute(
                "DELETE FROM bot_settings WHERE key IN (?, ?)",
                (self._db_key(guild_id, "channel"), self._db_key(guild_id, "message")),
            )
            conn.commit()
        except Exception as e:
            logger.debug("Failed to clear player message ids: %s", e)

    def _get_channel(self, guild_id: int) -> Optional[discord.TextChannel]:
        guild = self.bot.get_guild(guild_id)
        if not guild:
            return None
        # Prefer configured music channel
        ch = guild.get_channel(self.bot.config.music_channel_id)
        if isinstance(ch, discord.TextChannel):
            return ch
        # Fallback: system channel
        if isinstance(guild.system_channel, discord.TextChannel):
            return guild.system_channel
        for c in guild.text_channels:
            if c.permissions_for(guild.me).send_messages:
                return c
        return None

    def _build_view(self, guild_id: int) -> PlayerView:
        return PlayerView(bot=self.bot, guild_id=guild_id)

    def _player_state(self, guild_id: int) -> dict:
        player = discord.utils.get(self.bot.voice_clients, guild__id=guild_id)
        loop = self.bot.queue_manager.get_loop(guild_id)
        queue_len = self.bot.queue_manager.get_length(guild_id)

        if not player or not getattr(player, "last_track", None) or not player.playing:
            return {
                "playing": False,
                "paused": False,
                "volume": 50,
                "loop": loop,
                "queue_len": queue_len,
                "autoplay": getattr(player, "autoplay_enabled", False) if player else False,
                "active_filter": getattr(player, "active_filter", "off") if player else "off",
            }

        track = player.last_track
        return {
            "playing": True,
            "paused": player.paused,
            "title": track.title,
            "author": track.author,
            "uri": track.uri,
            "length": track.length,
            "position": player.position if hasattr(player, "position") else 0,
            "thumbnail": getattr(track, "artwork_url", None),
            "volume": player.get_volume() if hasattr(player, "get_volume") else 50,
            "loop": loop,
            "queue_len": queue_len,
            "autoplay": getattr(player, "autoplay_enabled", False),
            "active_filter": getattr(player, "active_filter", "off"),
            "requester": None,
        }

    def build_embed(self, guild_id: int) -> discord.Embed:
        state = self._player_state(guild_id)
        if not state["playing"]:
            return EmbedManager.player_idle_embed(
                queue_len=state["queue_len"],
                loop=state["loop"],
            )
        return EmbedManager.player_now_playing_embed(
            title=state["title"],
            author=state["author"],
            uri=state["uri"],
            length=state["length"],
            position=state["position"],
            thumbnail_url=state.get("thumbnail"),
            volume=state["volume"],
            paused=state["paused"],
            loop=state["loop"],
            autoplay=state["autoplay"],
            queue_len=state["queue_len"],
            requester=state.get("requester"),
            active_filter=state.get("active_filter", "off"),
        )

    async def ensure_message(
        self,
        guild_id: int,
        channel: Optional[discord.abc.Messageable] = None,
    ) -> Optional[discord.Message]:
        """Get or create the persistent player message."""
        if guild_id in self._messages:
            try:
                # Touch to verify still exists
                await self._messages[guild_id].channel.fetch_message(self._messages[guild_id].id)
                return self._messages[guild_id]
            except (discord.NotFound, discord.HTTPException, AttributeError):
                self._messages.pop(guild_id, None)

        # Try load from DB
        channel_id, message_id = self._load_ids(guild_id)
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
                    self._clear_ids(guild_id)

        # Create new
        target = channel or self._get_channel(guild_id)
        if target is None:
            logger.warning("No channel to post player message for guild %s", guild_id)
            return None

        embed = self.build_embed(guild_id)
        view = self._build_view(guild_id)
        try:
            msg = await target.send(embed=embed, view=view)
            self._messages[guild_id] = msg
            self._save_ids(guild_id, msg.channel.id, msg.id)
            try:
                self.bot.add_view(view, message_id=msg.id)
            except Exception:
                pass
            logger.info("Created player message %s in guild %s", msg.id, guild_id)
            return msg
        except Exception as e:
            logger.error("Failed to create player message: %s", e)
            return None

    async def update_now_playing(self, guild_id: int) -> None:
        """Edit the player message to reflect current state."""
        msg = await self.ensure_message(guild_id)
        if not msg:
            return

        embed = self.build_embed(guild_id)
        view = self._build_view(guild_id)
        try:
            await msg.edit(embed=embed, view=view)
            self._messages[guild_id] = msg
        except discord.NotFound:
            self._messages.pop(guild_id, None)
            self._clear_ids(guild_id)
            await self.ensure_message(guild_id)
        except discord.HTTPException as e:
            logger.debug("Player message edit failed: %s", e)

        # Manage progress task
        state = self._player_state(guild_id)
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
                state = self._player_state(guild_id)
                if not state["playing"] or state["paused"]:
                    break
                msg = self._messages.get(guild_id)
                if not msg:
                    break
                embed = self.build_embed(guild_id)
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
        """On bot ready: re-bind persistent views and cache messages."""
        # Register a template view so buttons work after restart for any guild
        # We re-add per-guild views when we restore messages
        guild_id = getattr(self.bot.config, "guild_id", None)
        if not guild_id:
            return

        channel_id, message_id = self._load_ids(guild_id)
        if not channel_id or not message_id:
            return

        try:
            ch = self.bot.get_channel(channel_id) or await self.bot.fetch_channel(channel_id)
            msg = await ch.fetch_message(message_id)
            view = self._build_view(guild_id)
            self.bot.add_view(view, message_id=message_id)
            self._messages[guild_id] = msg
            # Refresh embed state
            await msg.edit(embed=self.build_embed(guild_id), view=view)
            logger.info("Restored player view for guild %s message %s", guild_id, message_id)
            state = self._player_state(guild_id)
            if state["playing"] and not state["paused"]:
                self.start_progress_task(guild_id)
        except Exception as e:
            logger.warning("Could not restore player message: %s", e)
