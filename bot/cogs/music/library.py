"""Library cog — favorites & playlists."""

import logging

import discord
import wavelink
from discord.ext import commands

from bot.core.errors import DifferentVoiceChannel, NotInVoiceChannel, build_error_embed
from bot.database import favorites_manager, playlist_manager
from bot.music.embed_manager import EmbedManager
from bot.music.emoji import EMOJI
from bot.music.views import FavoritesPaginatorView, PlaylistDetailView, PlaylistListView

from .base import check_guild_and_channel, get_player_from_ctx, is_authorized, MusicCogMixin

logger = logging.getLogger(__name__)


class LibraryCog(commands.Cog, MusicCogMixin):
    def __init__(self, bot):
        self.bot = bot

    async def _check_guild_and_channel(self, ctx):
        return await check_guild_and_channel(ctx, self.bot.config)

    async def _require_authorized(self, ctx):
        return await is_authorized(ctx, self.bot)

    async def _ensure_voice(self, ctx):
        if not ctx.author.voice or not ctx.author.voice.channel:
            raise NotInVoiceChannel()
        voice_channel = ctx.author.voice.channel
        existing = discord.utils.get(self.bot.voice_clients, guild__id=ctx.guild.id)
        if existing and existing.channel != voice_channel:
            raise DifferentVoiceChannel()
        if existing:
            return voice_channel, existing
        player = await self.bot.lavalink.get_player(ctx.guild.id, voice_channel)
        return voice_channel, player

    async def _play_track(self, ctx, player, track: wavelink.Playable):
        from bot.database import guild_settings

        settings = guild_settings.get(str(ctx.guild.id), self.bot.config.database_path)
        await player.set_volume(settings.get("volume", 50))
        if player.playing:
            position = self.bot.queue_manager.add(
                ctx.guild.id,
                track,
                ctx.author.id,
            )
            embed = EmbedManager.track_added(
                title=track.title,
                uri=track.uri,
                position=position,
                queue_length=self.bot.queue_manager.get_length(ctx.guild.id),
                duration=track.length,
                thumbnail_url=getattr(track, "artwork_url", None),
            )
            await self._send_embed_to_response(ctx, embed, delete_after=10)
            if hasattr(self.bot, "player_messages"):
                await self.bot.player_messages.update_now_playing(ctx.guild.id)
        else:
            await player.play(track)
            self.bot.queue_manager.add_history(
                ctx.guild.id,
                track,
            )
            if hasattr(self.bot, "player_messages"):
                await self.bot.player_messages.update_now_playing(ctx.guild.id)
            else:
                embed = EmbedManager.now_playing(
                    title=track.title,
                    author=track.author,
                    uri=track.uri,
                    length=track.length,
                    thumbnail_url=getattr(track, "artwork_url", None),
                    requester=ctx.author.mention,
                    volume=settings.get("volume", 50),
                    active_filter=getattr(player, "active_filter", "off"),
                )
                await self._send_embed_to_response(ctx, embed)

    async def _run_controller(self, ctx, coro):
        result = await coro
        color = discord.Color.green() if result.ok else discord.Color.red()
        await self._send_embed_to_response(
            ctx,
            embed=discord.Embed(description=result.message, color=color),
            delete_after=8 if result.ok else 12,
        )
        if result.refresh_player and hasattr(self.bot, "player_messages"):
            await self.bot.player_messages.update_now_playing(ctx.guild.id)

    @commands.command(name="favorite", aliases=["fav", "like"])
    async def favorite(self, ctx):
        if not await self._check_guild_and_channel(ctx):
            return
        if not await self._require_authorized(ctx):
            return
        await self._run_controller(
            ctx, self.bot.player_controller.favorite(ctx.guild.id, ctx.author)
        )

    @commands.command(name="favorites")
    async def favorites(self, ctx, page: int = 1):
        if not await self._check_guild_and_channel(ctx):
            return
        if not await self._require_authorized(ctx):
            return
        favs, total = favorites_manager.get_favorites(
            user_id=str(ctx.author.id), page=page, db_path=self.bot.config.database_path
        )
        embed = EmbedManager.favorites_embed(favorites=favs, page=page, total=total)
        if total == 0:
            await self._send_embed_to_response(ctx, embed)
            return
        view = FavoritesPaginatorView(
            bot=self.bot,
            guild_id=ctx.guild.id,
            user_id=ctx.author.id,
            initial_page=page,
            page_size=10,
        )
        await self._send_to_response(ctx, embed=embed, view=view)

    @commands.command(name="playlist_create")
    async def playlist_create(self, ctx, name: str, *, description: str = ""):
        if not await self._check_guild_and_channel(ctx):
            return
        if not await self._require_authorized(ctx):
            return
        playlist_id = playlist_manager.create_playlist(
            user_id=str(ctx.author.id),
            guild_id=str(ctx.guild.id),
            name=name,
            description=description,
            db_path=self.bot.config.database_path,
        )
        if playlist_id:
            embed = discord.Embed(
                title="📀 Playlist Created",
                description=f"**{name}** has been created.",
                color=discord.Color.green(),
            )
            embed.set_footer(text=f"ID: {playlist_id}")
        else:
            embed = build_error_embed(description=f"You already have a playlist named **{name}**.")
        await self._send_embed_to_response(ctx, embed)

    @commands.command(name="playlists")
    async def playlists(self, ctx):
        if not await self._check_guild_and_channel(ctx):
            return
        if not await self._require_authorized(ctx):
            return
        playlists = playlist_manager.list_user_playlists(
            user_id=str(ctx.author.id), db_path=self.bot.config.database_path
        )
        if not playlists:
            await self._send_embed_to_response(
                ctx,
                embed=build_error_embed(
                    description="You have no playlists. Create one with `!playlist_create <name>`."
                ),
            )
            return
        embed = discord.Embed(
            title=f"{EMOJI['music']} Your Playlists",
            description=f"You have **{len(playlists)}** playlist(s). Select one to view tracks and play.",
            color=discord.Color.purple(),
        )
        lines = []
        for pl in playlists[:10]:
            lines.append(
                f"**{pl.get('name')}** — `{pl.get('track_count', 0)}` tracks — ID: `{pl.get('playlist_id')[:8]}...`"
            )
        if lines:
            embed.add_field(name="Playlists", value="\n".join(lines), inline=False)
        embed.set_footer(text="Use the dropdown to browse • !playlist_show <id> for direct view")
        view = PlaylistListView(
            bot=self.bot, guild_id=ctx.guild.id, user_id=ctx.author.id, playlists=playlists
        )
        await self._send_to_response(ctx, embed=embed, view=view)

    @commands.command(name="playlist_show", aliases=["playlist_view", "pl_show"])
    async def playlist_show(self, ctx, playlist_id: str, page: int = 1):
        if not await self._check_guild_and_channel(ctx):
            return
        if not await self._require_authorized(ctx):
            return
        playlist = playlist_manager.get_playlist(
            playlist_id=playlist_id, db_path=self.bot.config.database_path
        )
        if not playlist:
            await self._send_embed_to_response(ctx, embed=build_error_embed(description="Playlist not found."))
            return
        if not playlist.get("tracks"):
            await self._send_embed_to_response(ctx, embed=build_error_embed(description="This playlist has no tracks."))
            return
        view = PlaylistDetailView(
            bot=self.bot,
            guild_id=ctx.guild.id,
            user_id=ctx.author.id,
            playlist=playlist,
            page=page,
            page_size=10,
        )
        embed = view._build_embed()
        await self._send_to_response(ctx, embed=embed, view=view)

    @commands.command(name="playlist_add")
    async def playlist_add(self, ctx, playlist_id: str):
        if not await self._check_guild_and_channel(ctx):
            return
        if not await self._require_authorized(ctx):
            return
        player = get_player_from_ctx(ctx)
        if not player or not player.playing or not player.last_track:
            await self._send_embed_to_response(ctx, embed=build_error_embed(description="Nothing is currently playing."))
            return
        track = player.last_track
        success = playlist_manager.add_track(
            playlist_id=playlist_id,
            title=track.title,
            author=track.author,
            uri=track.uri,
            identifier=track.identifier,
            length=track.length,
            added_by=str(ctx.author.id),
            artwork_url=getattr(track, "artwork_url", None),
            db_path=self.bot.config.database_path,
        )
        if success:
            embed = discord.Embed(
                title="✅ Track Added",
                description=f"Added **{track.title}** to the playlist.",
                color=discord.Color.green(),
            )
        else:
            embed = build_error_embed(
                description="Could not add track. Check the playlist ID or track limit."
            )
        await self._send_embed_to_response(ctx, embed)

    @commands.command(name="playlist_remove")
    async def playlist_remove(self, ctx, playlist_id: str, position: int):
        if not await self._check_guild_and_channel(ctx):
            return
        if not await self._require_authorized(ctx):
            return
        success = playlist_manager.remove_track(
            playlist_id=playlist_id,
            position=position,
            user_id=str(ctx.author.id),
            db_path=self.bot.config.database_path,
        )
        if success:
            embed = discord.Embed(
                title="✅ Track Removed",
                description=f"Removed track at position {position}.",
                color=discord.Color.green(),
            )
        else:
            embed = build_error_embed(
                description="Could not remove track. Check permissions or position."
            )
        await self._send_embed_to_response(ctx, embed)

    @commands.command(name="playlist_play")
    async def playlist_play(self, ctx, playlist_id: str):
        if not await self._check_guild_and_channel(ctx):
            return
        if not await self._require_authorized(ctx):
            return
        async with ctx.typing():
            playlist = playlist_manager.get_playlist(
                playlist_id=playlist_id, db_path=self.bot.config.database_path
            )
            if not playlist:
                await self._send_embed_to_response(ctx, embed=build_error_embed(description="Playlist not found."))
                return
            if not playlist["tracks"]:
                await self._send_embed_to_response(ctx, embed=build_error_embed(description="This playlist has no tracks."))
                return
            try:
                _voice_channel, player = await self._ensure_voice(ctx)
            except (NotInVoiceChannel, DifferentVoiceChannel) as e:
                await self._send_embed_to_response(ctx, embed=build_error_embed(description=e.user_message))
                return
            if not player:
                await self._send_embed_to_response(ctx, embed=build_error_embed(description="Failed to connect to voice."))
                return
            for track_data in playlist["tracks"]:
                try:
                    tracks = await wavelink.Playable.search(track_data["uri"])
                    if tracks:
                        wavelink_track = tracks[0]
                        await self._play_track(ctx, player, wavelink_track)
                except Exception as e:
                    logger.debug("Failed to queue track %s: %s", track_data.get("title"), e)
            embed = discord.Embed(
                title="📀 Playing Playlist",
                description=f"Queued **{len(playlist['tracks'])}** tracks from **{playlist['name']}**.",
                color=discord.Color.purple(),
            )
            await self._send_embed_to_response(ctx, embed)


async def setup(bot):
    await bot.add_cog(LibraryCog(bot))
