"""Playlist views."""
from __future__ import annotations

import logging
import math
from typing import List

import discord
import wavelink

from bot.database import guild_settings, playlist_manager
from bot.music.embed_manager import EmbedManager
from bot.music.emoji import EMOJI
from .base import auth_ok, ensure_voice_player_shared, play_wavelink_track_shared

logger = logging.getLogger(__name__)


class PlaylistSelect(discord.ui.Select):
    def __init__(self, playlists: List[dict], user_id: int, bot, guild_id: int):
        self.playlists = playlists
        self.bot = bot
        self.guild_id = guild_id
        self.user_id = user_id

        options = []
        for pl in playlists[:25]:
            name = (pl.get("name") or "Untitled")[:80]
            count = pl.get("track_count", 0)
            desc = f"{count} tracks"
            if pl.get("description"):
                desc = (pl.get("description")[:60] + f" • {count} tracks")[:100]
            options.append(
                discord.SelectOption(
                    label=name[:100], description=desc[:100], value=str(pl.get("playlist_id")), emoji="📀"
                )
            )
        if not options:
            options.append(discord.SelectOption(label="No playlists", value="none", description="Create one with !playlist_create"))

        super().__init__(
            placeholder="📀 Choose a playlist...",
            min_values=1,
            max_values=1,
            options=options,
            row=0,
            disabled=len(playlists) == 0,
        )

    async def callback(self, interaction: discord.Interaction):
        ok, err = auth_ok(self.bot, interaction.user.id)
        if not ok:
            await interaction.response.send_message(err, ephemeral=True)
            return
        if self.values[0] == "none":
            await interaction.response.send_message("No playlist.", ephemeral=True)
            return

        playlist_id = self.values[0]
        await interaction.response.defer()

        playlist = playlist_manager.get_playlist(playlist_id=playlist_id, db_path=self.bot.config.database_path)
        if not playlist:
            await interaction.followup.send(f"{EMOJI['error']} Playlist not found.", ephemeral=True)
            return

        view = PlaylistDetailView(self.bot, self.guild_id, interaction.user.id, playlist, page=1)
        embed = view._build_embed()
        await interaction.followup.send(embed=embed, view=view, ephemeral=True)


class PlaylistListView(discord.ui.View):
    def __init__(self, bot, guild_id: int, user_id: int, playlists: List[dict]):
        super().__init__(timeout=90)
        self.bot = bot
        self.guild_id = guild_id
        self.user_id = user_id
        self.add_item(PlaylistSelect(playlists, user_id, bot, guild_id))

    @discord.ui.button(label="Close", style=discord.ButtonStyle.danger, emoji="❌", row=1)
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
            try:
                await interaction.response.edit_message(view=self)
            except Exception:
                pass


class PlaylistTrackSelect(discord.ui.Select):
    def __init__(self, tracks_page: List[dict], playlist_id: str, bot, guild_id: int, user_id: int):
        self.tracks_page = tracks_page
        self.bot = bot
        self.guild_id = guild_id
        self.user_id = user_id
        self.playlist_id = playlist_id

        options = []
        for t in tracks_page:
            dur = EmbedManager._format_duration(t.get("length", 0))
            title = (t.get("title") or "Unknown")[:80]
            author = (t.get("author") or "")[:30]
            pos = t.get("position", "?")
            label = f"{pos}. {title}"[:100]
            desc = f"{author} • {dur}"[:100]
            options.append(discord.SelectOption(label=label, description=desc, value=str(t.get("position")), emoji="🎵"))
        if not options:
            options.append(discord.SelectOption(label="No tracks on this page", value="none"))

        super().__init__(
            placeholder="🎵 Play a track from playlist...",
            min_values=1,
            max_values=1,
            options=options[:25],
            row=0,
            disabled=len(tracks_page) == 0,
        )

    async def callback(self, interaction: discord.Interaction):
        ok, err = auth_ok(self.bot, interaction.user.id)
        if not ok:
            await interaction.response.send_message(err, ephemeral=True)
            return
        if self.values[0] == "none":
            await interaction.response.send_message("No track.", ephemeral=True)
            return

        pos = int(self.values[0])
        track_data = next((t for t in self.tracks_page if t.get("position") == pos), None)
        if not track_data:
            await interaction.response.send_message(f"{EMOJI['error']} Track not found.", ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)

        guild = self.bot.get_guild(self.guild_id)
        member = guild.get_member(interaction.user.id) if guild else None
        if not member:
            member = interaction.user  # type: ignore

        uri = track_data.get("uri")
        try:
            tracks = await wavelink.Playable.search(uri)
        except Exception as e:
            await interaction.followup.send(f"{EMOJI['error']} Search failed: {e}", ephemeral=True)
            return
        if not tracks:
            await interaction.followup.send(f"{EMOJI['error']} Track not found.", ephemeral=True)
            return

        w_track = tracks[0]
        try:
            playing, embed, _ = await play_wavelink_track_shared(self.bot, self.guild_id, member, w_track)
        except ValueError as ve:
            await interaction.followup.send(str(ve), ephemeral=True)
            return
        except Exception as e:
            logger.exception("Playlist track play failed")
            await interaction.followup.send(f"{EMOJI['error']} Failed: {e}", ephemeral=True)
            return

        await interaction.followup.send(embed=embed, ephemeral=True)


class PlaylistDetailView(discord.ui.View):
    def __init__(self, bot, guild_id: int, user_id: int, playlist: dict, page: int = 1, page_size: int = 10):
        super().__init__(timeout=180)
        self.bot = bot
        self.guild_id = guild_id
        self.user_id = user_id
        self.playlist = playlist
        self.current_page = max(1, page)
        self.page_size = page_size
        self.playlist_id = playlist.get("playlist_id")
        self._refresh_components()

    def _get_page_tracks(self):
        all_tracks = self.playlist.get("tracks", [])
        start = (self.current_page - 1) * self.page_size
        end = start + self.page_size
        return all_tracks[start:end], len(all_tracks)

    def _build_embed(self) -> discord.Embed:
        tracks_page, total_tracks = self._get_page_tracks()
        embed = EmbedManager.playlist_embed(
            playlist=self.playlist, page=self.current_page, page_size=self.page_size
        )
        return embed

    def _refresh_components(self):
        for child in list(self.children):
            if isinstance(child, PlaylistTrackSelect):
                self.remove_item(child)

        tracks_page, total = self._get_page_tracks()
        select = PlaylistTrackSelect(tracks_page, self.playlist_id, self.bot, self.guild_id, self.user_id)
        self.add_item(select)

        total_overall = len(self.playlist.get("tracks", []))
        total_pages = max(1, math.ceil(total_overall / self.page_size)) if total_overall else 1
        for child in self.children:
            if isinstance(child, discord.ui.Button):
                lbl = (child.label or "").lower()
                if "prev" in lbl:
                    child.disabled = self.current_page <= 1
                elif "next" in lbl and "prev" not in lbl:
                    if "play" not in lbl:
                        child.disabled = self.current_page >= total_pages
                elif "play all" in lbl:
                    child.disabled = total_overall == 0

    @discord.ui.button(emoji="◀️", label="Prev", style=discord.ButtonStyle.secondary, row=1)
    async def prev_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        ok, err = auth_ok(self.bot, interaction.user.id)
        if not ok:
            await interaction.response.send_message(err, ephemeral=True)
            return
        if self.current_page > 1:
            self.current_page -= 1
        self._refresh_components()
        embed = self._build_embed()
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(emoji="▶️", label="Next", style=discord.ButtonStyle.secondary, row=1)
    async def next_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        ok, err = auth_ok(self.bot, interaction.user.id)
        if not ok:
            await interaction.response.send_message(err, ephemeral=True)
            return
        total_overall = len(self.playlist.get("tracks", []))
        total_pages = max(1, math.ceil(total_overall / self.page_size))
        if self.current_page < total_pages:
            self.current_page += 1
        self._refresh_components()
        embed = self._build_embed()
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(emoji="▶️", label="Play All", style=discord.ButtonStyle.primary, row=1)
    async def play_all(self, interaction: discord.Interaction, button: discord.ui.Button):
        ok, err = auth_ok(self.bot, interaction.user.id)
        if not ok:
            await interaction.response.send_message(err, ephemeral=True)
            return
        await interaction.response.defer(ephemeral=True)

        guild = self.bot.get_guild(self.guild_id)
        member = guild.get_member(interaction.user.id) if guild else None
        if not member:
            member = interaction.user  # type: ignore

        tracks = self.playlist.get("tracks", [])
        if not tracks:
            await interaction.followup.send(f"{EMOJI['error']} Playlist empty.", ephemeral=True)
            return

        queued = 0
        for td in tracks:
            try:
                w_tracks = await wavelink.Playable.search(td.get("uri"))
                if not w_tracks:
                    continue
                w_track = w_tracks[0]
                voice_channel, player = await ensure_voice_player_shared(self.bot, self.guild_id, member)
                settings = guild_settings.get(str(self.guild_id), self.bot.config.database_path)
                vol = settings.get("volume", 50)
                try:
                    await player.set_volume(vol)
                except Exception:
                    pass

                if player.playing:
                    self.bot.queue_manager.add(
                        self.guild_id,
                        {
                            "title": w_track.title,
                            "author": w_track.author,
                            "uri": w_track.uri,
                            "identifier": w_track.identifier,
                            "length": w_track.length,
                            "artwork_url": getattr(w_track, "artwork_url", None),
                        },
                        member.id,
                    )
                else:
                    await player.play(w_track)
                    self.bot.queue_manager.add_history(
                        self.guild_id,
                        {
                            "title": w_track.title,
                            "author": w_track.author,
                            "uri": w_track.uri,
                            "identifier": w_track.identifier,
                            "length": w_track.length,
                            "requester_id": member.id,
                        },
                    )
                queued += 1
            except Exception as e:
                logger.debug("Failed to queue playlist track %s: %s", td.get("title"), e)
                continue

        if hasattr(self.bot, "player_messages"):
            try:
                await self.bot.player_messages.update_now_playing(self.guild_id)
            except Exception:
                pass

        await interaction.followup.send(f"{EMOJI['ok']} Queued **{queued}** tracks from **{self.playlist.get('name')}**.", ephemeral=True)

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
            try:
                await interaction.response.edit_message(view=self)
            except Exception:
                pass

    async def on_timeout(self):
        for child in self.children:
            child.disabled = True
