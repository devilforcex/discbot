"""
FastAPI web dashboard for the Discord Music Bot.
Glassmorphic Nightmare Music UI + REST API for monitoring and control.
"""

import logging
from pathlib import Path
from typing import Any, Optional

import discord
import wavelink

logger = logging.getLogger(__name__)

# Check if FastAPI and uvicorn are available
try:
    from fastapi import FastAPI, Request, HTTPException, Depends
    from fastapi.responses import HTMLResponse, JSONResponse
    from fastapi.staticfiles import StaticFiles
    from fastapi.templating import Jinja2Templates
    from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
    import uvicorn

    HAS_FASTAPI = True
except ImportError:
    HAS_FASTAPI = False
    FastAPI = None
    uvicorn = None
    HTTPBearer = None


class DashboardServer:
    """Optional FastAPI web dashboard server.

    Runs as an isolated background task alongside the Discord bot.
    Serves the Nightmare-style glass UI and REST endpoints.
    """

    def __init__(self, bot):
        self.bot = bot
        self._app = None
        self._server = None
        self._templates = None
        self._running = False

    async def start(self) -> None:
        """Start the FastAPI server in background."""
        if not HAS_FASTAPI:
            logger.warning(
                "Dashboard dependencies not installed. "
                "Install: pip install fastapi uvicorn jinja2 aiofiles python-multipart"
            )
            return

        self._app = FastAPI(title="DiscBot · Nightmare Music Dashboard")

        base = Path(__file__).parent
        template_dir = base / "templates"
        static_dir = base / "static"
        template_dir.mkdir(parents=True, exist_ok=True)
        static_dir.mkdir(parents=True, exist_ok=True)
        (static_dir / "css").mkdir(parents=True, exist_ok=True)
        (static_dir / "js").mkdir(parents=True, exist_ok=True)

        self._templates = Jinja2Templates(directory=str(template_dir))
        self._app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

        self._register_routes()

        config = self.bot.config
        self._server = uvicorn.Server(
            config=uvicorn.Config(
                app=self._app,
                host=config.dashboard_host,
                port=config.dashboard_port,
                log_level="warning",
            )
        )

        self._running = True
        logger.info(
            "Dashboard available at http://%s:%s",
            config.dashboard_host,
            config.dashboard_port,
        )

        # Run uvicorn (blocking serve) — caller should create_task
        await self._server.serve()

    async def stop(self) -> None:
        """Stop the dashboard server."""
        self._running = False
        if self._server:
            self._server.should_exit = True
            logger.info("Dashboard server stopped")

    def _check_write_auth(self, credentials: Optional[Any]) -> None:
        """Validate Bearer token against dashboard_secret_key for write ops."""
        secret = getattr(self.bot.config, "dashboard_secret_key", "") or ""
        if not secret or secret == "change_me_to_a_random_secret_key":
            # Dev default: allow local control without strict auth when secret unset
            return
        if credentials is None or credentials.credentials != secret:
            raise HTTPException(status_code=401, detail="Invalid or missing Bearer token")

    def _register_routes(self) -> None:
        """Register all dashboard routes."""
        app = self._app
        bot = self.bot
        templates = self._templates
        security = HTTPBearer(auto_error=False)

        # ============================================================
        # API Routes
        # ============================================================

        @app.get("/api/health")
        async def api_health():
            return {"ok": True, "ready": bot.is_ready()}

        @app.get("/api/status")
        async def api_bot_status():
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

        @app.get("/api/lavalink")
        async def api_lavalink_status():
            try:
                node = wavelink.Pool.get_node()
                if node:
                    return {
                        "connected": True,
                        "uri": node.uri,
                        "latency_ms": round(node.latency, 2) if node.latency else None,
                        "players": node.stats.players if node.stats else 0,
                        "playing_players": node.stats.playing_players if node.stats else 0,
                    }
            except Exception:
                pass
            return {"connected": False}

        @app.get("/api/queue/{guild_id}")
        async def api_queue(guild_id: int):
            queue = bot.queue_manager.get_all(guild_id)
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
                raise HTTPException(status_code=500, detail=str(e))

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
                raise HTTPException(status_code=500, detail=str(e))

        @app.post("/api/settings/{guild_id}")
        async def api_update_settings(
            guild_id: str,
            request: Request,
            credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
        ):
            self._check_write_auth(credentials)
            from bot.database import guild_settings as gs

            data = await request.json()
            try:
                settings = gs.set(guild_id, bot.config.database_path, **data)
                return {"success": True, "settings": settings}
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))

        @app.get("/api/favorites/{user_id}")
        async def api_favorites(user_id: str, page: int = 1):
            from bot.database import favorites_manager as fm

            try:
                favs, total = fm.get_favorites(
                    user_id, page=page, db_path=bot.config.database_path
                )
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
                raise HTTPException(status_code=500, detail=str(e))

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
                raise HTTPException(status_code=500, detail=str(e))

        @app.post("/api/control/{guild_id}/{action}")
        async def api_control(
            guild_id: int,
            action: str,
            request: Request,
            credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
        ):
            """Remote playback control (pause/resume/skip/stop/shuffle/volume)."""
            self._check_write_auth(credentials)

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
                raise HTTPException(status_code=500, detail=str(e))

        # ============================================================
        # HTML — Nightmare glass UI
        # ============================================================

        @app.get("/", response_class=HTMLResponse)
        async def index(request: Request):
            guild_id = str(getattr(bot.config, "guild_id", "") or "")
            return templates.TemplateResponse(
                "index.html",
                {
                    "request": request,
                    "guild_id": guild_id,
                },
            )
