"""Favorites paginator views."""

from __future__ import annotations

import contextlib
import logging
import math

import discord
import wavelink

from bot.database import favorites_manager
from bot.music.embed_manager import EmbedManager
from bot.music.emoji import EMOJI

from .base import auth_ok, play_wavelink_track_shared

logger = logging.getLogger(__name__)


class FavoriteSelect(discord.ui.Select):
    def __init__(self, favorites_page: list[dict], user_id: int, bot, guild_id: int):
        self.favorites_page = favorites_page
        self.bot = bot
        self.guild_id = guild_id
        self.owner_id = user_id

        options = []
        for fav in favorites_page:
            dur = EmbedManager._format_duration(fav.get("length", 0))
            title = (fav.get("title") or "Unknown")[:80]
            author = (fav.get("author") or "")[:40]
            label = title[:100]
            desc = f"{author} • {dur}"[:100]
            options.append(
                discord.SelectOption(
                    label=label, description=desc, value=str(fav.get("identifier")), emoji="⭐"
                )
            )
        if not options:
            options.append(
                discord.SelectOption(
                    label="No favorites on this page", value="none", description=""
                )
            )

        super().__init__(
            placeholder="⭐ Play a favorite...",
            min_values=1,
            max_values=1,
            options=options[:25],
            row=0,
            disabled=len(favorites_page) == 0,
        )

    async def callback(self, interaction: discord.Interaction):
        ok, err = auth_ok(self.bot, interaction.user.id)
        if not ok:
            await interaction.response.send_message(err, ephemeral=True)
            return
        if self.values[0] == "none":
            await interaction.response.send_message("No track selected.", ephemeral=True)
            return

        identifier = self.values[0]
        fav = next((f for f in self.favorites_page if str(f.get("identifier")) == identifier), None)
        if not fav:
            await interaction.response.send_message(
                f"{EMOJI['error']} Favorite not found.", ephemeral=True
            )
            return

        await interaction.response.defer(ephemeral=True)

        guild = self.bot.get_guild(self.guild_id)
        member = guild.get_member(interaction.user.id) if guild else None
        if not member:
            member = interaction.user  # type: ignore

        uri = fav.get("uri")
        try:
            tracks = await wavelink.Playable.search(uri)
        except Exception as e:
            await interaction.followup.send(f"{EMOJI['error']} Search failed: {e}", ephemeral=True)
            return

        if not tracks:
            await interaction.followup.send(
                f"{EMOJI['error']} Track not found on Lavalink.", ephemeral=True
            )
            return

        w_track = tracks[0]
        try:
            _, embed, _ = await play_wavelink_track_shared(
                self.bot, self.guild_id, member, w_track
            )
        except ValueError as ve:
            await interaction.followup.send(str(ve), ephemeral=True)
            return
        except Exception as e:
            logger.exception("Favorite play failed")
            await interaction.followup.send(f"{EMOJI['error']} Failed: {e}", ephemeral=True)
            return

        await interaction.followup.send(embed=embed, ephemeral=True)


class FavoritesPaginatorView(discord.ui.View):
    def __init__(
        self, bot, guild_id: int, user_id: int, initial_page: int = 1, page_size: int = 10
    ):
        super().__init__(timeout=120)
        self.bot = bot
        self.guild_id = guild_id
        self.user_id = user_id
        self.current_page = max(1, initial_page)
        self.page_size = page_size
        self._refresh_select()

    def _fetch_page(self):
        favs, total = favorites_manager.get_favorites(
            user_id=str(self.user_id),
            page=self.current_page,
            page_size=self.page_size,
            db_path=self.bot.config.database_path,
        )
        return favs, total

    def _build_embed(self) -> discord.Embed:
        favs, total = self._fetch_page()
        embed = EmbedManager.favorites_embed(
            favorites=favs, page=self.current_page, total=total, page_size=self.page_size
        )
        return embed

    def _total_pages(self) -> int:
        _, total = self._fetch_page()
        return max(1, math.ceil(total / self.page_size)) if total else 1

    def _refresh_select(self):
        for child in list(self.children):
            if isinstance(child, FavoriteSelect):
                self.remove_item(child)
        favs, _ = self._fetch_page()
        select = FavoriteSelect(favs, self.user_id, self.bot, self.guild_id)
        self.add_item(select)

        total = self._total_pages()
        for child in self.children:
            if isinstance(child, discord.ui.Button):
                lbl = (child.label or "").lower()
                if "prev" in lbl or (child.emoji and str(child.emoji) == "◀️" and lbl != "close"):
                    child.disabled = self.current_page <= 1
                if "next" in lbl and "prev" not in lbl:
                    child.disabled = self.current_page >= total

    @discord.ui.button(emoji="◀️", label="Prev", style=discord.ButtonStyle.secondary, row=1)
    async def prev_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        ok, err = auth_ok(self.bot, interaction.user.id)
        if not ok:
            await interaction.response.send_message(err, ephemeral=True)
            return
        if interaction.user.id != self.user_id and interaction.user.id != self.bot.config.owner_id:
            await interaction.response.send_message(
                f"{EMOJI['error']} Only your own favorites.", ephemeral=True
            )
            return
        if self.current_page > 1:
            self.current_page -= 1
        self._refresh_select()
        embed = self._build_embed()
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(emoji="▶️", label="Next", style=discord.ButtonStyle.secondary, row=1)
    async def next_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        ok, err = auth_ok(self.bot, interaction.user.id)
        if not ok:
            await interaction.response.send_message(err, ephemeral=True)
            return
        if interaction.user.id != self.user_id and interaction.user.id != self.bot.config.owner_id:
            await interaction.response.send_message(
                f"{EMOJI['error']} Only your own favorites.", ephemeral=True
            )
            return
        if self.current_page < self._total_pages():
            self.current_page += 1
        self._refresh_select()
        embed = self._build_embed()
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(emoji="❌", label="Close", style=discord.ButtonStyle.danger, row=1)
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
            child.disabled = True
