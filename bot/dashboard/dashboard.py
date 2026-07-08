"""
FastAPI web dashboard for the Discord Music Bot.
Provides a lightweight, optional web interface for monitoring and managing the bot.
"""

import logging
from pathlib import Path
from typing import Optional

import discord
import wavelink

logger = logging.getLogger(__name__)

# Check if FastAPI and uvicorn are available
try:
    from fastapi import FastAPI, Request, Form, HTTPException
    from fastapi.responses import HTMLResponse, JSONResponse
    from fastapi.templating import Jinja2Templates
    import uvicorn
    HAS_FASTAPI = True
except ImportError:
    HAS_FASTAPI = False
    FastAPI = None
    uvicorn = None


class DashboardServer:
    """Optional FastAPI web dashboard server.

    Runs as an isolated background task alongside the Discord bot.
    Provides REST API and HTML pages for monitoring bot status,
    Lavalink status, queue, favorites, playlists, and guild settings.

    This server is fully optional; the bot functions without it.
    """

    def __init__(self, bot):
        """Initialize the dashboard server.

        Args:
            bot: The Bot instance.
        """
        self.bot = bot
        self._app = None
        self._server = None
        self._templates = None
        self._running = False

    async def start(self) -> None:
        """Start the FastAPI server in background.

        If dependencies are missing, logs a warning and exits gracefully.
        """
        if not HAS_FASTAPI:
            logger.warning(
                "Dashboard dependencies not installed. "
                "Install: pip install fastapi uvicorn jinja2 aiofiles python-multipart"
            )
            return

        self._app = FastAPI(title="Discord Music Bot Dashboard")

        # Setup templates directory
        template_dir = Path(__file__).parent / "templates"
        template_dir.mkdir(parents=True, exist_ok=True)
        self._templates = Jinja2Templates(directory=str(template_dir))

        # Register routes
        self._register_routes()

        # Start server
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

    async def stop(self) -> None:
        """Stop the dashboard server."""
        self._running = False
        if self._server:
            await self._server.shutdown()
            logger.info("Dashboard server stopped")

    def _register_routes(self) -> None:
        """Register all dashboard routes."""
        app = self._app
        bot = self.bot

        # ============================================================
        # API Routes
        # ============================================================

        @app.get("/api/status")
        async def api_bot_status():
            """API: Get bot status information."""
            return {
                "bot_name": str(bot.user) if bot.user else "Not ready",
                "bot_id": bot.user.id if bot.user else None,
                "latency_ms": round(bot.latency * 1000, 2),
                "guild_count": len(bot.guilds),
                "uptime_seconds": None,  # Could track start time
                "connected_voice_channels": len(bot.voice_clients),
            }

        @app.get("/api/lavalink")
        async def api_lavalink_status():
            """API: Get Lavalink node status."""
            try:
                node = wavelink.Pool.get_node()
                if node:
                    return {
                        "connected": True,
                        "uri": node.uri,
                        "latency_ms": round(node.latency, 2),
                        "players": node.stats.players if node.stats else 0,
                        "playing_players": node.stats.playing_players if node.stats else 0,
                    }
            except Exception:
                pass
            return {"connected": False}

        @app.get("/api/queue/{guild_id}")
        async def api_queue(guild_id: int):
            """API: Get queue for a guild."""
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
            """API: Get currently playing track."""
            player = discord.utils.get(bot.voice_clients, guild__id=guild_id)
            if player and player.playing and player.last_track:
                track = player.last_track
                return {
                    "playing": True,
                    "title": track.title,
                    "author": track.author,
                    "uri": track.uri,
                    "length": track.length,
                    "position": player.position if hasattr(player, "position") else 0,
                    "paused": player.paused,
                    "volume": player.get_volume(),
                    "artwork_url": getattr(track, "artwork_url", None),
                }
            return {"playing": False}

        @app.get("/api/stats/{guild_id}")
        async def api_stats(guild_id: str):
            """API: Get playback statistics for a guild."""
            from bot.database import history_manager as hm
            try:
                stats = hm.get_stats(guild_id, bot.config.database_path)
                return stats
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))

        @app.get("/api/settings/{guild_id}")
        async def api_get_settings(guild_id: str):
            """API: Get guild settings."""
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
        ):
            """API: Update guild settings."""
            from bot.database import guild_settings as gs
            data = await request.json()
            try:
                settings = gs.set(guild_id, bot.config.database_path, **data)
                return {"success": True, "settings": settings}
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))

        @app.get("/api/favorites/{user_id}")
        async def api_favorites(user_id: str, page: int = 1):
            """API: Get user favorites."""
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
            """API: Get user playlists."""
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

        # ============================================================
        # HTML Routes (simple status page)
        # ============================================================

        @app.get("/", response_class=HTMLResponse)
        async def index():
            """Dashboard home page."""
            node_status = "Disconnected"
            try:
                node = wavelink.Pool.get_node()
                if node:
                    node_status = f"Connected ({round(node.latency, 1)}ms)"
            except Exception:
                pass

            html = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Discord Music Bot Dashboard</title>
                <meta charset="utf-8">
                <meta name="viewport" content="width=device-width, initial-scale=1">
                <style>
                    body {{
                        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                        background: #1a1a2e;
                        color: #eee;
                        margin: 0;
                        padding: 20px;
                    }}
                    .container {{ max-width: 900px; margin: 0 auto; }}
                    h1 {{ color: #e94560; }}
                    .card {{
                        background: #16213e;
                        border-radius: 8px;
                        padding: 20px;
                        margin: 15px 0;
                    }}
                    .status {{ display: inline-block; padding: 4px 12px; border-radius: 12px; font-size: 0.9em; }}
                    .online {{ background: #2ecc71; color: #fff; }}
                    .offline {{ background: #e74c3c; color: #fff; }}
                    .stat-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }}
                    .stat-label {{ color: #888; font-size: 0.85em; }}
                    .stat-value {{ font-size: 1.1em; font-weight: bold; }}
                    a {{ color: #e94560; text-decoration: none; }}
                    a:hover {{ text-decoration: underline; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <h1>🎵 Music Bot Dashboard</h1>

                    <div class="card">
                        <h2>🤖 Bot Status</h2>
                        <div class="stat-grid">
                            <div>
                                <div class="stat-label">Status</div>
                                <div class="stat-value">
                                    <span class="status {'online' if bot.is_ready() else 'offline'}">
                                        {'Online' if bot.is_ready() else 'Offline'}
                                    </span>
                                </div>
                            </div>
                            <div>
                                <div class="stat-label">Name</div>
                                <div class="stat-value">{str(bot.user) if bot.user else 'N/A'}</div>
                            </div>
                            <div>
                                <div class="stat-label">Latency</div>
                                <div class="stat-value">{round(bot.latency * 1000, 1)}ms</div>
                            </div>
                            <div>
                                <div class="stat-label">Guilds</div>
                                <div class="stat-value">{len(bot.guilds)}</div>
                            </div>
                            <div>
                                <div class="stat-label">Voice Connections</div>
                                <div class="stat-value">{len(bot.voice_clients)}</div>
                            </div>
                        </div>
                    </div>

                    <div class="card">
                        <h2>🎧 Lavalink</h2>
                        <div class="stat-grid">
                            <div>
                                <div class="stat-label">Status</div>
                                <div class="stat-value">
                                    <span class="status {'online' if 'Connected' in node_status else 'offline'}">
                                        {'Connected' if 'Connected' in node_status else 'Disconnected'}
                                    </span>
                                </div>
                            </div>
                            <div>
                                <div class="stat-label">Latency</div>
                                <div class="stat-value">{node_status.split('(')[-1].rstrip(')') if 'Connected' in node_status else 'N/A'}</div>
                            </div>
                        </div>
                    </div>

                    <div class="card">
                        <h2>📊 Quick Links</h2>
                        <ul>
                            <li><a href="/api/status">API: Bot Status</a></li>
                            <li><a href="/api/lavalink">API: Lavalink Status</a></li>
                        </ul>
                        <p><small>Use the API endpoints for guild-specific data: /api/queue/<guild_id>, /api/nowplaying/<guild_id></small></p>
                    </div>

                    <div class="card">
                        <h2>📋 Connected Guilds</h2>
                        <ul>
            """
            for guild in bot.guilds:
                voice = discord.utils.get(bot.voice_clients, guild__id=guild.id)
                status = "🔊" if voice else "🔇"
                html += f"<li>{status} <strong>{guild.name}</strong> (ID: {guild.id})</li>\n"

            html += """
                        </ul>
                    </div>
                </div>
            </body>
            </html>
            """
            return HTMLResponse(content=html)