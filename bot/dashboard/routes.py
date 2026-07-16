"""API routes for dashboard — split from monolithic dashboard.py."""

from __future__ import annotations

import logging
from typing import Any

import discord
from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

# pyright: reportUnusedFunction=false


class SettingsUpdate(BaseModel):
    """Validated payload for settings updates."""

    volume: int | None = Field(None, ge=0, le=100)
    autoplay: bool | None = None
    announce_songs: bool | None = None
    default_source: str | None = Field(None, pattern=r"^(ytsearch|ytmsearch|scsearch)$")


def register_routes(app, bot, security, check_write_auth):
    """Register all dashboard routes on FastAPI app."""

    @app.get("/api/health")
    async def api_health():
        return {"ok": True, "ready": bot.is_ready()}

    @app.get("/api/health/lavalink")
    async def api_lavalink_health():
        if hasattr(bot, "lavalink") and bot.lavalink:
            health = await bot.lavalink.health_check()
            return health
        return {"healthy": False, "reason": "Lavalink client not initialized"}

    async def _status_payload() -> dict[str, Any]:
        uptime = None
        if hasattr(bot, "get_uptime"):
            try:
                uptime = await bot.get_uptime()
            except Exception:
                uptime = None
        return {
            "bot_name": str(bot.user) if bot.user else "Not ready",
            "bot_id": bot.user.id if bot.user else None,
            "latency_ms": round(bot.latency * 1000, 2) if bot.latency else None,
            "guild_count": len(bot.guilds),
            "uptime": uptime,
            "uptime_seconds": None,
            "connected_voice_channels": len(bot.voice_clients),
        }

    def _guild_payload(guild: Any) -> dict[str, Any]:
        return {
            "id": guild.id,
            "name": guild.name,
            "member_count": getattr(guild, "member_count", None),
            "icon_url": str(guild.icon.url) if getattr(guild, "icon", None) else None,
        }

    def _coerce_bool(value: Any) -> bool:
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            normalized = value.strip().lower()
            if normalized in {"1", "true", "yes", "on"}:
                return True
            if normalized in {"0", "false", "no", "off"}:
                return False
        return bool(value)

    @app.get("/api/status")
    async def api_bot_status():
        return await _status_payload()

    @app.get("/api/guilds")
    async def api_guilds():
        """Return the guilds visible to the bot for dashboard selectors."""
        return {"guilds": [_guild_payload(guild) for guild in bot.guilds]}

    @app.get("/api/lavalink")
    async def api_lavalink_status():
        try:
            # Use the bot's Lavalink client health check for consistency
            health = await bot.lavalink.health_check()
            if health.get("connected"):
                return {
                    "connected": True,
                    "uri": health.get("uri"),
                    "latency_ms": None,  # Not in health check, could be added
                    "players": health.get("players", 0),
                    "playing_players": 0,  # Not in health check
                }
        except Exception:
            logger.warning("Lavalink status check failed")
        return {"connected": False}

    @app.get("/api/queue/{guild_id}")
    async def api_queue(guild_id: int):
        queue = bot.queue_manager.get_all_as_dicts(guild_id)
        return {
            "guild_id": guild_id,
            "queue_length": len(queue),
            "tracks": [
                {
                    "title": t.get("title"),
                    "author": t.get("author"),
                    "uri": t.get("uri"),
                    "length": t.get("length"),
                    "requester_id": t.get("requester_id"),
                }
                for t in queue
            ],
        }

    @app.get("/api/nowplaying/{guild_id}")
    async def api_now_playing(guild_id: int):
        player = discord.utils.get(bot.voice_clients, guild__id=guild_id)
        if player and getattr(player, "playing", False) and getattr(player, "last_track", None):
            track = player.last_track
            loop_mode = None
            try:
                mode = bot.queue_manager.get_loop(guild_id)
                loop_mode = mode.value if hasattr(mode, "value") else str(mode)
            except Exception:
                pass
            return {
                "playing": True,
                "title": track.title,
                "author": track.author,
                "uri": track.uri,
                "length": track.length,
                "position": player.position if hasattr(player, "position") else 0,
                "paused": player.paused,
                "volume": player.get_volume() if hasattr(player, "get_volume") else 50,
                "artwork_url": getattr(track, "artwork_url", None),
                "autoplay": getattr(player, "autoplay_enabled", False),
                "loop": loop_mode,
                "queue_length": bot.queue_manager.get_length(guild_id),
            }
        return {"playing": False, "queue_length": bot.queue_manager.get_length(guild_id)}

    @app.get("/api/stats/{guild_id}")
    async def api_stats(guild_id: str):
        from bot.database import history_manager as hm

        try:
            return hm.get_stats(guild_id, bot.config.database_path)
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e)) from None

    @app.get("/api/history/{guild_id}")
    async def api_history(guild_id: str, limit: int = 10):
        """Return recent playback history for a guild."""
        from bot.database import history_manager as hm

        try:
            safe_limit = max(1, min(50, int(limit)))
            return {
                "guild_id": guild_id,
                "limit": safe_limit,
                "tracks": hm.get_recent(guild_id, safe_limit, bot.config.database_path),
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e)) from None

    @app.get("/api/overview/{guild_id}")
    async def api_overview(guild_id: int):
        """Combined dashboard payload to reduce frontend round-trips."""
        from bot.database import guild_settings as gs
        from bot.database import history_manager as hm

        try:
            status = await _status_payload()
            queue = bot.queue_manager.get_all_as_dicts(guild_id)
            guild = bot.get_guild(guild_id) if hasattr(bot, "get_guild") else None
            return {
                "status": status,
                "guild": _guild_payload(guild) if guild else {"id": guild_id, "name": None},
                "queue_length": len(queue),
                "settings": gs.get(str(guild_id), bot.config.database_path),
                "stats": hm.get_stats(str(guild_id), bot.config.database_path),
                "recent": hm.get_recent(str(guild_id), 10, bot.config.database_path),
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e)) from None

    @app.get("/api/settings/{guild_id}")
    async def api_get_settings(guild_id: str):
        from bot.database import guild_settings as gs

        try:
            settings = gs.get(guild_id, bot.config.database_path)
            return {
                "guild_id": guild_id,
                "volume": settings.get("volume", 50),
                "autoplay": bool(settings.get("autoplay", True)),
                "announce_songs": bool(settings.get("announce_songs", True)),
                "default_source": settings.get("default_source", "ytsearch"),
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e)) from None

    @app.post("/api/settings/{guild_id}")
    async def api_update_settings(
        guild_id: str,
        payload: SettingsUpdate,
        credentials: HTTPAuthorizationCredentials | None = Depends(security),
    ):
        check_write_auth(credentials)
        from bot.database import guild_settings as gs

        updates = payload.model_dump(exclude_unset=True)
        if "autoplay" in updates:
            updates["autoplay"] = _coerce_bool(updates["autoplay"])
        if "announce_songs" in updates:
            updates["announce_songs"] = _coerce_bool(updates["announce_songs"])
        settings = gs.set(guild_id, bot.config.database_path, **updates)
        return {"success": True, "settings": settings}

    @app.get("/api/favorites/{user_id}")
    async def api_favorites(user_id: str, page: int = 1):
        from bot.database import favorites_manager as fm

        try:
            favs, total = fm.get_favorites(user_id, page=page, db_path=bot.config.database_path)
            return {
                "user_id": user_id,
                "page": page,
                "total": total,
                "favorites": [
                    {
                        "title": f["title"],
                        "author": f["author"],
                        "uri": f["uri"],
                        "length": f["length"],
                    }
                    for f in favs
                ],
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e)) from None

    @app.get("/api/playlists/{user_id}")
    async def api_playlists(user_id: str):
        from bot.database import playlist_manager as pm

        try:
            playlists = pm.list_user_playlists(user_id, bot.config.database_path)
            return {
                "user_id": user_id,
                "playlists": [
                    {
                        "playlist_id": p["playlist_id"],
                        "name": p["name"],
                        "description": p.get("description", ""),
                        "track_count": p.get("track_count", 0),
                        "created_at": p.get("created_at"),
                    }
                    for p in playlists
                ],
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e)) from None

    @app.post("/api/control/{guild_id}/{action}")
    async def api_control(
        guild_id: int,
        action: str,
        request: Request,
        credentials: HTTPAuthorizationCredentials | None = Depends(security),
    ):
        check_write_auth(credentials)
        body: dict = {}
        try:
            body = await request.json()
        except Exception:
            body = {}

        player = discord.utils.get(bot.voice_clients, guild__id=guild_id)
        action = action.lower().strip()

        if action in ("pause", "resume", "play_pause", "skip", "stop", "shuffle") and not player:
            raise HTTPException(status_code=400, detail="No active player for this guild")

        try:
            if action == "pause":
                if not player.playing:
                    raise HTTPException(status_code=400, detail="Nothing playing")
                await player.pause(True)
                return {"success": True, "message": "Paused"}

            if action == "resume":
                if not player.paused:
                    raise HTTPException(status_code=400, detail="Not paused")
                await player.pause(False)
                return {"success": True, "message": "Resumed"}

            if action == "play_pause":
                if player.paused:
                    await player.pause(False)
                    return {"success": True, "message": "Resumed"}
                if player.playing:
                    await player.pause(True)
                    return {"success": True, "message": "Paused"}
                raise HTTPException(status_code=400, detail="Nothing playing")

            if action == "skip":
                if not player.playing:
                    raise HTTPException(status_code=400, detail="Nothing playing")
                await player.stop()
                return {"success": True, "message": "Skipped"}

            if action == "stop":
                await player.stop()
                bot.queue_manager.clear(guild_id)
                return {"success": True, "message": "Stopped and cleared queue"}

            if action == "shuffle":
                if bot.queue_manager.is_empty(guild_id):
                    raise HTTPException(status_code=400, detail="Queue is empty")
                bot.queue_manager.shuffle(guild_id)
                return {"success": True, "message": "Queue shuffled"}

            if action == "volume":
                vol = int(body.get("volume", 50))
                vol = max(0, min(100, vol))
                if not player:
                    raise HTTPException(status_code=400, detail="No active player")
                await player.set_volume(vol)
                try:
                    from bot.database import guild_settings as gs

                    gs.set(str(guild_id), bot.config.database_path, volume=vol)
                except Exception:
                    pass
                return {"success": True, "message": f"Volume set to {vol}%", "volume": vol}

            raise HTTPException(status_code=400, detail=f"Unknown action: {action}")
        except HTTPException:
            raise
        except Exception as e:
            logger.exception("Control action %s failed", action)
            raise HTTPException(status_code=500, detail=str(e)) from None
