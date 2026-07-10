"""PlayerView — persistent controls, refactored to use services."""
from __future__ import annotations

import logging
import time
from typing import Optional

import discord

from bot.music.emoji import EMOJI
from bot.music.embed_manager import EmbedManager
from .filter_select import FilterSelect, CID_PREFIX

logger = logging.getLogger(__name__)

COOLDOWN_SECONDS = 1.0


class PlayerView(discord.ui.View):
    def __init__(self, bot=None, guild_id: Optional[int] = None):
        super().__init__(timeout=None)
        self.bot = bot
        self.guild_id = guild_id
        self._cooldowns: dict[int, float] = {}
        gid = guild_id or 0
        self.clear_items()
        self._build_components(gid)

    def _build_components(self, guild_id: int) -> None:
        self.add_item(FilterSelect(bot=self.bot, guild_id=guild_id))
        self.add_item(self._btn(EMOJI["play_pause"], "play_pause", guild_id, 1, discord.ButtonStyle.primary))
        self.add_item(self._btn(EMOJI["skip"], "skip", guild_id, 1, discord.ButtonStyle.secondary))
        self.add_item(self._btn(EMOJI["stop"], "stop", guild_id, 1, discord.ButtonStyle.secondary))
        self.add_item(self._btn(EMOJI["shuffle"], "shuffle", guild_id, 1, discord.ButtonStyle.secondary))
        self.add_item(self._btn(EMOJI["loop_queue"], "loop", guild_id, 1, discord.ButtonStyle.secondary))
        self.add_item(self._btn(EMOJI["vol_down"], "vol_down", guild_id, 2, discord.ButtonStyle.secondary))
        self.add_item(self._btn(EMOJI["vol_up"], "vol_up", guild_id, 2, discord.ButtonStyle.secondary))
        self.add_item(self._btn(EMOJI["favorite"], "favorite", guild_id, 2, discord.ButtonStyle.secondary))
        self.add_item(self._btn(EMOJI["queue"], "queue", guild_id, 2, discord.ButtonStyle.secondary))
        self.add_item(self._btn(EMOJI["disconnect"], "disconnect", guild_id, 2, discord.ButtonStyle.danger))
        self.add_item(self._btn("⏮️", "replay", guild_id, 3, discord.ButtonStyle.secondary))
        self.add_item(self._btn("⏪", "seek_back", guild_id, 3, discord.ButtonStyle.secondary))
        self.add_item(self._btn("⏩", "seek_fwd", guild_id, 3, discord.ButtonStyle.secondary))

    def _btn(self, emoji: str, action: str, guild_id: int, row: int, style: discord.ButtonStyle) -> discord.ui.Button:
        button = discord.ui.Button(emoji=emoji, style=style, custom_id=f"{CID_PREFIX}:{action}:{guild_id}", row=row)
        button.callback = self._make_callback(action)
        return button

    def _make_callback(self, action: str):
        async def callback(interaction: discord.Interaction):
            await self._handle(interaction, action)

        return callback

    def _parse_guild_id(self, interaction: discord.Interaction) -> Optional[int]:
        if self.guild_id:
            return self.guild_id
        try:
            custom_id = interaction.data.get("custom_id", "")
            parts = custom_id.split(":")
            if len(parts) >= 3:
                return int(parts[2])
        except Exception:
            pass
        if interaction.guild:
            return interaction.guild.id
        return None

    def _on_cooldown(self, user_id: int) -> bool:
        now = time.monotonic()
        last = self._cooldowns.get(user_id, 0)
        if now - last < COOLDOWN_SECONDS:
            return True
        self._cooldowns[user_id] = now
        return False

    async def _handle(self, interaction: discord.Interaction, action: str) -> None:
        bot = self.bot or interaction.client
        guild_id = self._parse_guild_id(interaction)
        if not guild_id:
            await interaction.response.send_message(f"{EMOJI['error']} Could not resolve guild.", ephemeral=True)
            return
        if self._on_cooldown(interaction.user.id):
            await interaction.response.send_message(f"{EMOJI['error']} Slow down a second.", ephemeral=True)
            return

        controller = getattr(bot, "player_controller", None)
        if controller is None:
            from bot.music.player_controller import PlayerController

            controller = PlayerController(bot)
            bot.player_controller = controller

        user = interaction.user
        if not isinstance(user, discord.Member):
            await interaction.response.send_message(f"{EMOJI['error']} Guild members only.", ephemeral=True)
            return

        if action == "queue":
            ok, err = controller.check_authorized(user.id)
            if not ok:
                await interaction.response.send_message(err, ephemeral=True)
                return
            await interaction.response.defer(ephemeral=True)
            player = controller.get_player(guild_id)
            current = None
            if player and player.playing and player.last_track:
                t = player.last_track
                current = {
                    "title": t.title,
                    "author": t.author,
                    "uri": t.uri,
                    "length": t.length,
                    "requester_id": getattr(t, "requester_id", user.id),
                }
            queue_list = bot.queue_manager.get_all(guild_id)
            if not queue_list and not current:
                await interaction.followup.send(f"{EMOJI['error']} The queue is empty.", ephemeral=True)
                return
            embed = EmbedManager.queue_embed(
                queue=queue_list,
                current_track=current,
                page=1,
                guild_name=interaction.guild.name if interaction.guild else "Server",
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)

        result = None
        try:
            if action == "play_pause":
                result = await controller.play_pause(guild_id, user)
            elif action == "skip":
                result = await controller.skip(guild_id, user)
            elif action == "stop":
                result = await controller.stop(guild_id, user)
            elif action == "shuffle":
                result = await controller.shuffle(guild_id, user)
            elif action == "loop":
                result = await controller.cycle_loop(guild_id, user)
            elif action == "vol_down":
                result = await controller.volume_delta(guild_id, user, -10)
            elif action == "vol_up":
                result = await controller.volume_delta(guild_id, user, 10)
            elif action == "favorite":
                result = await controller.favorite(guild_id, user)
            elif action == "disconnect":
                result = await controller.disconnect(guild_id, user)
            elif action == "seek_fwd":
                result = await controller.seek_forward(guild_id, user, 10)
            elif action == "seek_back":
                result = await controller.seek_backward(guild_id, user, 10)
            elif action == "replay":
                result = await controller.replay(guild_id, user)
            else:
                await interaction.followup.send(f"{EMOJI['error']} Unknown action.", ephemeral=True)
                return
        except Exception as e:
            logger.exception("Player button %s failed", action)
            await interaction.followup.send(f"{EMOJI['error']} Action failed: {e}", ephemeral=True)
            return

        await interaction.followup.send(result.message, ephemeral=True)
        if result.refresh_player:
            mgr = getattr(bot, "player_messages", None)
            if mgr:
                try:
                    await mgr.update_now_playing(guild_id)
                except Exception as e:
                    logger.debug("Player message refresh failed: %s", e)


def make_persistent_view(bot, guild_id: int = 0) -> PlayerView:
    return PlayerView(bot=bot, guild_id=guild_id)
