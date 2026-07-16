"""Search view — TrackSelect + SearchView."""

from __future__ import annotations

import contextlib
import logging

import discord
import wavelink

from bot.music.embed_manager import EmbedManager
from bot.music.emoji import EMOJI

from .base import auth_ok, play_wavelink_track_shared

logger = logging.getLogger(__name__)


class TrackSelect(discord.ui.Select):
    def __init__(self, tracks: list[wavelink.Playable], requester_id: int, bot, guild_id: int):
        self.tracks = tracks[:5]
        self.bot = bot
        self.guild_id = guild_id
        self.requester_id = requester_id

        options = []
        for idx, t in enumerate(self.tracks):
            dur = EmbedManager._format_duration(t.length)
            title = (t.title or "Unknown")[:80]
            author = (t.author or "Unknown")[:40]
            label = f"{idx + 1}. {title}"[:100]
            desc = f"{author} • {dur}"[:100]
            options.append(
                discord.SelectOption(label=label, description=desc, value=str(idx), emoji="🎵")
            )

        super().__init__(
            placeholder="🎶 Избери песен...",
            min_values=1,
            max_values=1,
            options=options,
            row=0,
        )

    async def callback(self, interaction: discord.Interaction):
        ok, err = auth_ok(self.bot, interaction.user.id)
        if not ok:
            await interaction.response.send_message(err, ephemeral=True)
            return

        idx = int(self.values[0])
        track = self.tracks[idx]

        await interaction.response.defer()

        guild = self.bot.get_guild(self.guild_id)
        member = guild.get_member(interaction.user.id) if guild else None
        if not member:
            member = interaction.user  # type: ignore

        try:
            _, embed, _ = await play_wavelink_track_shared(self.bot, self.guild_id, member, track)
        except ValueError as ve:
            await interaction.followup.send(str(ve), ephemeral=True)
            return
        except Exception as e:
            logger.exception("Failed to play selected track")
            await interaction.followup.send(f"{EMOJI['error']} Failed to play: {e}", ephemeral=True)
            return

        view: SearchView = self.view  # type: ignore
        for child in view.children:
            child.disabled = True
        view.stop()

        with contextlib.suppress(Exception):
            await interaction.message.edit(view=view)

        await interaction.followup.send(embed=embed)


class SearchView(discord.ui.View):
    def __init__(
        self, tracks: list[wavelink.Playable], requester_id: int, bot, guild_id: int, query: str
    ):
        super().__init__(timeout=60)
        self.bot = bot
        self.guild_id = guild_id
        self.query = query
        self.requester_id = requester_id
        self.tracks = tracks[:5]
        self.add_item(TrackSelect(self.tracks, requester_id, bot, guild_id))

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.secondary, emoji="❌", row=1)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        ok, err = auth_ok(self.bot, interaction.user.id)
        if not ok:
            await interaction.response.send_message(err, ephemeral=True)
            return
        if (
            interaction.user.id != self.requester_id
            and interaction.user.id != self.bot.config.owner_id
        ):
            await interaction.response.send_message(
                f"{EMOJI['error']} Only the requester can cancel.", ephemeral=True
            )
            return
        for child in self.children:
            child.disabled = True
        self.stop()
        await interaction.response.edit_message(
            content=f"{EMOJI['error']} Search canceled.", embed=None, view=self
        )

    async def on_timeout(self):
        for child in self.children:
            child.disabled = True
