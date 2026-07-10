"""Persistent filter select — extracted from player_view.py"""
from __future__ import annotations

import logging

import discord

from bot.music.audio_filters import get_filter_choices
from bot.music.emoji import EMOJI

logger = logging.getLogger(__name__)

CID_PREFIX = "mb"


class FilterSelect(discord.ui.Select):
    def __init__(self, bot=None, guild_id: int = 0):
        self.bot = bot
        self._gid = guild_id

        options = []
        for value, label, desc, emoji in get_filter_choices():
            options.append(
                discord.SelectOption(
                    label=label[:100],
                    description=desc[:100],
                    value=value,
                    emoji=emoji,
                )
            )

        super().__init__(
            placeholder="Select A Filter To Apply.",
            min_values=1,
            max_values=1,
            options=options[:25],
            custom_id=f"{CID_PREFIX}:filter:{guild_id}",
            row=0,
        )

    async def callback(self, interaction: discord.Interaction):
        bot = self.bot or interaction.client
        guild_id = self._gid
        if not guild_id:
            try:
                cid = interaction.data.get("custom_id", "")
                parts = cid.split(":")
                if len(parts) >= 3:
                    guild_id = int(parts[2])
            except Exception:
                pass
        if not guild_id and interaction.guild:
            guild_id = interaction.guild.id

        if not guild_id:
            await interaction.response.send_message(f"{EMOJI['error']} Could not resolve guild.", ephemeral=True)
            return

        from bot.music.player_controller import PlayerController

        controller = getattr(bot, "player_controller", None)
        if controller is None:
            controller = PlayerController(bot)
            bot.player_controller = controller

        user = interaction.user
        if not isinstance(user, discord.Member):
            await interaction.response.send_message(f"{EMOJI['error']} Guild members only.", ephemeral=True)
            return

        ok, err = controller.check_authorized(user.id)
        if not ok:
            await interaction.response.send_message(err, ephemeral=True)
            return

        filter_name = self.values[0]
        await interaction.response.defer(ephemeral=True)

        result = await controller.set_filter(guild_id, user, filter_name)
        await interaction.followup.send(result.message, ephemeral=True)

        if result.refresh_player:
            mgr = getattr(bot, "player_messages", None)
            if mgr:
                try:
                    await mgr.update_now_playing(guild_id)
                except Exception as e:
                    logger.debug("Player message refresh after filter failed: %s", e)
