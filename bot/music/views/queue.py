"""Queue paginator view."""

from __future__ import annotations

import contextlib
import logging
import math

import discord

from bot.music.embed_manager import EmbedManager
from bot.music.emoji import EMOJI

from .base import auth_ok

logger = logging.getLogger(__name__)


class QueuePaginatorView(discord.ui.View):
    def __init__(
        self, bot, guild_id: int, requester_id: int, guild_name: str = "Server", page: int = 1
    ):
        super().__init__(timeout=90)
        self.bot = bot
        self.guild_id = guild_id
        self.requester_id = requester_id
        self.guild_name = guild_name
        self.current_page = max(1, page)
        self._update_button_state()

    def _get_total_pages(self) -> int:
        queue_len = self.bot.queue_manager.get_length(self.guild_id)
        return max(1, math.ceil(queue_len / 10)) if queue_len else 1

    def _build_embed(self) -> discord.Embed:
        queue_list = self.bot.queue_manager.get_all_as_dicts(self.guild_id)
        player = discord.utils.get(self.bot.voice_clients, guild__id=self.guild_id)
        current_track = None
        if player and getattr(player, "playing", False) and getattr(player, "last_track", None):
            t = player.last_track
            current_track = {
                "title": t.title,
                "author": t.author,
                "uri": t.uri,
                "length": t.length,
                "requester_id": getattr(t, "requester_id", self.requester_id),
            }
        embed = EmbedManager.queue_embed(
            queue=queue_list,
            current_track=current_track,
            page=self.current_page,
            page_size=10,
            guild_name=self.guild_name,
        )
        return embed

    def _update_button_state(self):
        total = self._get_total_pages()
        for child in self.children:
            if isinstance(child, discord.ui.Button):
                if child.label == "Prev" or (child.emoji and str(child.emoji) == "◀️"):
                    child.disabled = self.current_page <= 1
                if child.label == "Next" or (child.emoji and str(child.emoji) == "▶️"):
                    child.disabled = self.current_page >= total

    @discord.ui.button(emoji="◀️", label="Prev", style=discord.ButtonStyle.secondary, row=0)
    async def prev_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        ok, err = auth_ok(self.bot, interaction.user.id)
        if not ok:
            await interaction.response.send_message(err, ephemeral=True)
            return
        if self.current_page > 1:
            self.current_page -= 1
        self._update_button_state()
        embed = self._build_embed()
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(emoji="▶️", label="Next", style=discord.ButtonStyle.secondary, row=0)
    async def next_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        ok, err = auth_ok(self.bot, interaction.user.id)
        if not ok:
            await interaction.response.send_message(err, ephemeral=True)
            return
        total = self._get_total_pages()
        if self.current_page < total:
            self.current_page += 1
        self._update_button_state()
        embed = self._build_embed()
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(emoji="🔀", label="Shuffle", style=discord.ButtonStyle.secondary, row=0)
    async def shuffle_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        ok, err = auth_ok(self.bot, interaction.user.id)
        if not ok:
            await interaction.response.send_message(err, ephemeral=True)
            return
        if self.bot.queue_manager.is_empty(self.guild_id):
            await interaction.response.send_message(
                f"{EMOJI['error']} Queue is empty.", ephemeral=True
            )
            return
        self.bot.queue_manager.shuffle(self.guild_id)
        embed = self._build_embed()
        await interaction.response.edit_message(embed=embed, view=self)
        await interaction.followup.send(f"{EMOJI['shuffle']} Queue shuffled.", ephemeral=True)

    @discord.ui.button(emoji="🔄", label="Refresh", style=discord.ButtonStyle.secondary, row=0)
    async def refresh_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        ok, err = auth_ok(self.bot, interaction.user.id)
        if not ok:
            await interaction.response.send_message(err, ephemeral=True)
            return
        self._update_button_state()
        embed = self._build_embed()
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(emoji="❌", label="Close", style=discord.ButtonStyle.danger, row=0)
    async def close_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        ok, err = auth_ok(self.bot, interaction.user.id)
        if not ok:
            await interaction.response.send_message(err, ephemeral=True)
            return
        for child in self.children:
            child.disabled = True
        self.stop()
        try:
            await interaction.message.delete()
        except Exception:
            with contextlib.suppress(Exception):
                await interaction.response.edit_message(view=self)

    async def on_timeout(self):
        for child in self.children:
            if isinstance(child, discord.ui.Button):
                child.disabled = True
