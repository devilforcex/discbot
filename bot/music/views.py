"""
Interactive views for Phase 2: search select, queue pagination, favorites, playlists.
Non-persistent (timeout based).
"""

from __future__ import annotations

import logging
import math
from typing import List

import discord
import wavelink

from bot.database import favorites_manager, guild_settings, playlist_manager
from bot.music.embed_manager import EmbedManager
from bot.music.emoji import EMOJI

logger = logging.getLogger(__name__)

# ------------------------------------------------------------
# Helpers
# ------------------------------------------------------------

def _is_url(query: str) -> bool:
    q = query.strip().lower()
    return (
        q.startswith("http://")
        or q.startswith("https://")
        or "youtube.com" in q
        or "youtu.be" in q
        or "spotify.com" in q
        or "soundcloud.com" in q
        or "music.youtube" in q
    )


def _auth_ok(bot, user_id: int) -> tuple[bool, str]:
    """Re-use PlayerController auth logic without importing circularly."""
    # owner bypass
    if user_id == bot.config.owner_id:
        return True, ""
    try:
        from bot.database.database import get_connection

        uid = str(user_id)
        conn = get_connection(bot.config.database_path)
        cur = conn.cursor()
        cur.execute("SELECT 1 FROM blacklisted_users WHERE user_id = ?", (uid,))
        if cur.fetchone():
            return False, f"{EMOJI['error']} You are blacklisted."
        cur.execute("SELECT 1 FROM approved_users WHERE user_id = ?", (uid,))
        if cur.fetchone():
            return True, ""
    except Exception as e:
        logger.debug("Auth check failed: %s", e)
    return False, f"{EMOJI['error']} You are not authorized to use this bot."


async def _ensure_voice_player(bot, guild_id: int, member: discord.Member):
    """Ensure member in voice and return (voice_channel, player). Raise if not."""
    if not member.voice or not member.voice.channel:
        raise ValueError(f"{EMOJI['error']} You must be in a voice channel.")
    voice_channel = member.voice.channel
    existing = discord.utils.get(bot.voice_clients, guild__id=guild_id)
    if existing and existing.channel != voice_channel:
        raise ValueError(f"{EMOJI['error']} You must be in the same voice channel as the bot.")
    if existing:
        return voice_channel, existing
    # create via lavalink client
    player = await bot.lavalink.get_player(guild_id, voice_channel)
    return voice_channel, player


async def _play_wavelink_track(bot, guild_id: int, member: discord.Member, track: wavelink.Playable):
    """Shared play-or-queue logic used by interactive views."""
    voice_channel, player = await _ensure_voice_player(bot, guild_id, member)

    settings = guild_settings.get(str(guild_id), bot.config.database_path)
    vol = settings.get("volume", 50)
    try:
        await player.set_volume(vol)
    except Exception:
        pass

    # If already playing, queue
    if player.playing:
        pos = bot.queue_manager.add(
            guild_id,
            {
                "title": track.title,
                "author": track.author,
                "uri": track.uri,
                "identifier": track.identifier,
                "length": track.length,
                "artwork_url": getattr(track, "artwork_url", None),
            },
            member.id,
        )
        embed = EmbedManager.track_added(
            title=track.title,
            uri=track.uri,
            position=pos,
            queue_length=bot.queue_manager.get_length(guild_id),
            duration=track.length,
        )
        # notify persistent player
        if hasattr(bot, "player_messages"):
            try:
                await bot.player_messages.update_now_playing(guild_id)
            except Exception as e:
                logger.debug("player_messages update failed: %s", e)
        return False, embed, track  # False = queued
    else:
        await player.play(track)
        bot.queue_manager.add_history(
            guild_id,
            {
                "title": track.title,
                "author": track.author,
                "uri": track.uri,
                "identifier": track.identifier,
                "length": track.length,
                "requester_id": member.id,
            },
        )
        if hasattr(bot, "player_messages"):
            try:
                await bot.player_messages.update_now_playing(guild_id)
            except Exception as e:
                logger.debug("player_messages update failed: %s", e)
        embed = EmbedManager.now_playing(
            title=track.title,
            author=track.author,
            uri=track.uri,
            length=track.length,
            thumbnail_url=getattr(track, "artwork_url", None),
            requester=member.mention,
            volume=vol,
        )
        return True, embed, track


# ------------------------------------------------------------
# 1) Search Select — top 5 results
# ------------------------------------------------------------

class TrackSelect(discord.ui.Select):
    def __init__(self, tracks: List[wavelink.Playable], requester_id: int, bot, guild_id: int):
        self.tracks = tracks[:5]
        self.bot = bot
        self.guild_id = guild_id
        self.requester_id = requester_id

        options = []
        for idx, t in enumerate(self.tracks):
            dur = EmbedManager._format_duration(t.length)
            title = (t.title or "Unknown")[:80]
            author = (t.author or "Unknown")[:40]
            # Label must be <=100 chars
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
        # Only original requester or owner can pick (soft)
        ok, err = _auth_ok(self.bot, interaction.user.id)
        if not ok:
            await interaction.response.send_message(err, ephemeral=True)
            return

        # Optionally restrict to requester + owner, but allow any authorized for collab
        # if interaction.user.id != self.requester_id and interaction.user.id != self.bot.config.owner_id:
        #     await interaction.response.send_message(f"{EMOJI['error']} Only the requester can pick.", ephemeral=True)
        #     return

        idx = int(self.values[0])
        track = self.tracks[idx]

        await interaction.response.defer()

        # Need member object for voice checks
        guild = self.bot.get_guild(self.guild_id)
        member = None
        if guild:
            member = guild.get_member(interaction.user.id)
        if not member:
            # fallback to interaction.user if DM? but should be Member
            member = interaction.user  # will fail voice check appropriately

        try:
            playing, embed, _ = await _play_wavelink_track(self.bot, self.guild_id, member, track)
        except ValueError as ve:
            await interaction.followup.send(str(ve), ephemeral=True)
            return
        except Exception as e:
            logger.exception("Failed to play selected track")
            await interaction.followup.send(f"{EMOJI['error']} Failed to play: {e}", ephemeral=True)
            return

        # Disable view after selection
        view: SearchView = self.view  # type: ignore
        for child in view.children:
            child.disabled = True
        view.stop()

        try:
            await interaction.message.edit(view=view)
        except Exception:
            pass

        await interaction.followup.send(embed=embed)


class SearchView(discord.ui.View):
    def __init__(self, tracks: List[wavelink.Playable], requester_id: int, bot, guild_id: int, query: str):
        super().__init__(timeout=60)
        self.bot = bot
        self.guild_id = guild_id
        self.query = query
        self.requester_id = requester_id
        self.tracks = tracks[:5]
        self.add_item(TrackSelect(self.tracks, requester_id, bot, guild_id))

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.secondary, emoji="❌", row=1)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        ok, err = _auth_ok(self.bot, interaction.user.id)
        if not ok:
            await interaction.response.send_message(err, ephemeral=True)
            return
        if interaction.user.id != self.requester_id and interaction.user.id != self.bot.config.owner_id:
            await interaction.response.send_message(f"{EMOJI['error']} Only the requester can cancel.", ephemeral=True)
            return
        for child in self.children:
            child.disabled = True
        self.stop()
        await interaction.response.edit_message(content=f"{EMOJI['error']} Search canceled.", embed=None, view=self)

    async def on_timeout(self):
        for child in self.children:
            child.disabled = True
        # try to edit original message if possible (we don't have reference, so skip)
        # The parent will handle externally if needed


# ------------------------------------------------------------
# 2) Queue Pagination View
# ------------------------------------------------------------

class QueuePaginatorView(discord.ui.View):
    def __init__(self, bot, guild_id: int, requester_id: int, guild_name: str = "Server", page: int = 1):
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
        queue_list = self.bot.queue_manager.get_all(self.guild_id)
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
        # Find buttons by custom method — we iterate children
        for child in self.children:
            if isinstance(child, discord.ui.Button):
                if child.label == "Prev" or (child.emoji and str(child.emoji) == "◀️"):
                    child.disabled = self.current_page <= 1
                if child.label == "Next" or (child.emoji and str(child.emoji) == "▶️"):
                    child.disabled = self.current_page >= total

    @discord.ui.button(emoji="◀️", label="Prev", style=discord.ButtonStyle.secondary, row=0)
    async def prev_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        ok, err = _auth_ok(self.bot, interaction.user.id)
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
        ok, err = _auth_ok(self.bot, interaction.user.id)
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
        ok, err = _auth_ok(self.bot, interaction.user.id)
        if not ok:
            await interaction.response.send_message(err, ephemeral=True)
            return
        if self.bot.queue_manager.is_empty(self.guild_id):
            await interaction.response.send_message(f"{EMOJI['error']} Queue is empty.", ephemeral=True)
            return
        self.bot.queue_manager.shuffle(self.guild_id)
        embed = self._build_embed()
        await interaction.response.edit_message(embed=embed, view=self)
        await interaction.followup.send(f"{EMOJI['shuffle']} Queue shuffled.", ephemeral=True)

    @discord.ui.button(emoji="🔄", label="Refresh", style=discord.ButtonStyle.secondary, row=0)
    async def refresh_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        ok, err = _auth_ok(self.bot, interaction.user.id)
        if not ok:
            await interaction.response.send_message(err, ephemeral=True)
            return
        self._update_button_state()
        embed = self._build_embed()
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(emoji="❌", label="Close", style=discord.ButtonStyle.danger, row=0)
    async def close_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Anyone authorized can close, or requester
        ok, err = _auth_ok(self.bot, interaction.user.id)
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
            if isinstance(child, discord.ui.Button):
                # keep close enabled? Disable all for safety
                child.disabled = True


# ------------------------------------------------------------
# 3) Favorites View — paginated + select to play
# ------------------------------------------------------------

class FavoriteSelect(discord.ui.Select):
    def __init__(self, favorites_page: List[dict], user_id: int, bot, guild_id: int):
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
            # value = identifier
            options.append(
                discord.SelectOption(
                    label=label, description=desc, value=str(fav.get("identifier")), emoji="⭐"
                )
            )
        if not options:
            options.append(discord.SelectOption(label="No favorites on this page", value="none", description=""))

        super().__init__(
            placeholder="⭐ Play a favorite...",
            min_values=1,
            max_values=1,
            options=options[:25],  # Discord limit 25
            row=0,
            disabled=len(favorites_page) == 0,
        )

    async def callback(self, interaction: discord.Interaction):
        ok, err = _auth_ok(self.bot, interaction.user.id)
        if not ok:
            await interaction.response.send_message(err, ephemeral=True)
            return
        if self.values[0] == "none":
            await interaction.response.send_message("No track selected.", ephemeral=True)
            return

        identifier = self.values[0]
        # Find fav dict
        fav = next((f for f in self.favorites_page if str(f.get("identifier")) == identifier), None)
        if not fav:
            await interaction.response.send_message(f"{EMOJI['error']} Favorite not found.", ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)

        guild = self.bot.get_guild(self.guild_id)
        member = guild.get_member(interaction.user.id) if guild else None
        if not member:
            member = interaction.user  # type: ignore

        # Search track by uri
        uri = fav.get("uri")
        try:
            tracks = await wavelink.Playable.search(uri)
        except Exception as e:
            await interaction.followup.send(f"{EMOJI['error']} Search failed: {e}", ephemeral=True)
            return

        if not tracks:
            await interaction.followup.send(f"{EMOJI['error']} Track not found on Lavalink.", ephemeral=True)
            return

        w_track = tracks[0]
        try:
            playing, embed, _ = await _play_wavelink_track(self.bot, self.guild_id, member, w_track)
        except ValueError as ve:
            await interaction.followup.send(str(ve), ephemeral=True)
            return
        except Exception as e:
            logger.exception("Favorite play failed")
            await interaction.followup.send(f"{EMOJI['error']} Failed: {e}", ephemeral=True)
            return

        await interaction.followup.send(embed=embed, ephemeral=True)


class FavoritesPaginatorView(discord.ui.View):
    def __init__(self, bot, guild_id: int, user_id: int, initial_page: int = 1, page_size: int = 10):
        super().__init__(timeout=120)
        self.bot = bot
        self.guild_id = guild_id
        self.user_id = user_id
        self.current_page = max(1, initial_page)
        self.page_size = page_size
        self._refresh_select()

    def _fetch_page(self):
        favs, total = favorites_manager.get_favorites(
            user_id=str(self.user_id), page=self.current_page, page_size=self.page_size, db_path=self.bot.config.database_path
        )
        return favs, total

    def _build_embed(self) -> discord.Embed:
        favs, total = self._fetch_page()
        embed = EmbedManager.favorites_embed(favorites=favs, page=self.current_page, total=total, page_size=self.page_size)
        return embed

    def _total_pages(self) -> int:
        _, total = self._fetch_page()
        return max(1, math.ceil(total / self.page_size)) if total else 1

    def _refresh_select(self):
        # Remove old select if exists
        for child in list(self.children):
            if isinstance(child, FavoriteSelect):
                self.remove_item(child)
        favs, _ = self._fetch_page()
        select = FavoriteSelect(favs, self.user_id, self.bot, self.guild_id)
        self.add_item(select)

        # Update button disabled states by label
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
        ok, err = _auth_ok(self.bot, interaction.user.id)
        if not ok:
            await interaction.response.send_message(err, ephemeral=True)
            return
        if interaction.user.id != self.user_id and interaction.user.id != self.bot.config.owner_id:
            await interaction.response.send_message(f"{EMOJI['error']} Only your own favorites.", ephemeral=True)
            return
        if self.current_page > 1:
            self.current_page -= 1
        self._refresh_select()
        embed = self._build_embed()
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(emoji="▶️", label="Next", style=discord.ButtonStyle.secondary, row=1)
    async def next_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        ok, err = _auth_ok(self.bot, interaction.user.id)
        if not ok:
            await interaction.response.send_message(err, ephemeral=True)
            return
        if interaction.user.id != self.user_id and interaction.user.id != self.bot.config.owner_id:
            await interaction.response.send_message(f"{EMOJI['error']} Only your own favorites.", ephemeral=True)
            return
        if self.current_page < self._total_pages():
            self.current_page += 1
        self._refresh_select()
        embed = self._build_embed()
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(emoji="❌", label="Close", style=discord.ButtonStyle.danger, row=1)
    async def close_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        ok, err = _auth_ok(self.bot, interaction.user.id)
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


# ------------------------------------------------------------
# 4) Playlist Views
# ------------------------------------------------------------

class PlaylistSelect(discord.ui.Select):
    """Select a playlist from user's list."""

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
            # trim description
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
        ok, err = _auth_ok(self.bot, interaction.user.id)
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

        # Show detailed view with its own paginator
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
        ok, err = _auth_ok(self.bot, interaction.user.id)
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
        ok, err = _auth_ok(self.bot, interaction.user.id)
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
            playing, embed, _ = await _play_wavelink_track(self.bot, self.guild_id, member, w_track)
        except ValueError as ve:
            await interaction.followup.send(str(ve), ephemeral=True)
            return
        except Exception as e:
            logger.exception("Playlist track play failed")
            await interaction.followup.send(f"{EMOJI['error']} Failed: {e}", ephemeral=True)
            return

        await interaction.followup.send(embed=embed, ephemeral=True)


class PlaylistDetailView(discord.ui.View):
    """Detailed playlist view with pagination + track select + Play All."""

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
        total_pages = max(1, math.ceil(total_tracks / self.page_size)) if total_tracks else 1
        embed = EmbedManager.playlist_embed(
            playlist=self.playlist, page=self.current_page, page_size=self.page_size
        )
        # Override footer with page info if needed — embed already has pagination
        return embed

    def _refresh_components(self):
        # Clear old TrackSelect
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
                    # next button (not play all)
                    if "play" not in lbl:
                        child.disabled = self.current_page >= total_pages
                elif "play all" in lbl:
                    child.disabled = total_overall == 0

    @discord.ui.button(emoji="◀️", label="Prev", style=discord.ButtonStyle.secondary, row=1)
    async def prev_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        ok, err = _auth_ok(self.bot, interaction.user.id)
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
        ok, err = _auth_ok(self.bot, interaction.user.id)
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
        ok, err = _auth_ok(self.bot, interaction.user.id)
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
                # Use shared play logic but avoid spamming embeds per track — queue directly after first
                voice_channel, player = await _ensure_voice_player(self.bot, self.guild_id, member)
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
        ok, err = _auth_ok(self.bot, interaction.user.id)
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
