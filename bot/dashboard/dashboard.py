"""
FastAPI web dashboard — refactored slim server.

Routes moved to routes.py for maintainability.
Glassmorphic Nightmare Music UI + REST API.
"""

import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

try:
    import uvicorn
    from fastapi import FastAPI
    from fastapi.security import HTTPBearer

    HAS_FASTAPI = True
except ImportError:
    HAS_FASTAPI = False
    FastAPI = None
    uvicorn = None
    HTTPBearer = None


class DashboardServer:
    """Optional FastAPI web dashboard server."""

    def __init__(self, bot):
        self.bot = bot
        self._app = None
        self._server = None
        self._running = False

    async def start(self) -> None:
        if not HAS_FASTAPI:
            logger.warning(
                "Dashboard dependencies not installed. Install: pip install fastapi uvicorn"
            )
            return

        from fastapi.middleware.cors import CORSMiddleware

        self._app = FastAPI(title="DrusaBoT · Nightmare Music Dashboard")  # type: ignore[misc]

        # CORS middleware - restrict to same origin by default, allow override via env
        import os

        cors_origins = os.environ.get("DASHBOARD_CORS_ORIGINS", "").split(",")
        cors_origins = [o.strip() for o in cors_origins if o.strip()] or ["*"]
        self._app.add_middleware(
            CORSMiddleware,
            allow_origins=cors_origins,
            allow_methods=["GET", "POST", "DELETE"],
            allow_headers=["*"],
        )

        base = Path(__file__).parent
        self._register_routes()

        # SPA catch-all: serve React build if available
        dist_dir = base.parent.parent / "web" / "dist"
        if dist_dir.is_dir():
            from fastapi import HTTPException
            from fastapi.responses import FileResponse

            @self._app.get("/{full_path:path}")
            async def serve_spa(full_path: str):  # pyright: ignore[reportUnusedFunction]
                if full_path.startswith("api/"):
                    raise HTTPException(status_code=404, detail="API endpoint not found")
                file_path = dist_dir / full_path
                if full_path and file_path.is_file():
                    return FileResponse(file_path)
                return FileResponse(dist_dir / "index.html")

        else:
            logger.warning(
                "React SPA build not found at %s. Run 'cd web && npm run build' to build the frontend.",
                dist_dir,
            )

        config = self.bot.config

        # Most PaaS platforms inject the listening port via $PORT and route
        # the healthcheck/traffic to it. Fall back to the configured port when $PORT
        # is not present (local dev).
        import os

        port = int(os.environ.get("PORT", str(config.dashboard_port or 18080)))

        # Bind to 0.0.0.0 by default so the server is reachable from outside the
        # container. When the config explicitly sets a host, honor it (e.g. local-only 127.0.0.1).
        host = config.dashboard_host if config.dashboard_host else "0.0.0.0"

        self._server = uvicorn.Server(
            config=uvicorn.Config(
                app=self._app,
                host=host,
                port=port,
                log_level="warning",
            )
        )

        self._running = True
        logger.info("Dashboard available at http://%s:%s", host, port)
        await self._server.serve()  # type: ignore[union-attr]

    async def stop(self) -> None:
        self._running = False
        if self._server:
            self._server.should_exit = True
            logger.info("Dashboard server stopped")

    def _check_write_auth(self, credentials: Any | None) -> None:
        secret = getattr(self.bot.config, "dashboard_secret_key", "") or ""
        if not secret or secret == "change_me_to_a_random_secret_key":
            from fastapi import HTTPException

            raise HTTPException(
                status_code=500,
                detail="Dashboard secret key not configured. Set DASHBOARD_SECRET_KEY in .env (must not be the default value).",
            )
        if credentials is None or credentials.credentials != secret:
            from fastapi import HTTPException

            raise HTTPException(status_code=401, detail="Invalid or missing Bearer token")

    def _register_routes(self) -> None:
        app = self._app
        bot = self.bot
        security = HTTPBearer(auto_error=False)  # type: ignore[call-arg]

        # Delegate to split routes module
        try:
            from .routes import register_routes

            register_routes(app, bot, security, self._check_write_auth)
        except ImportError as e:
            logger.error("Failed to load dashboard routes: %s", e)
            raise

        # WebSocket endpoint for real-time player updates
        from fastapi import WebSocket, WebSocketDisconnect

        from .ws_manager import ws_manager

        @app.websocket("/ws/{guild_id}")
        async def websocket_endpoint(websocket: WebSocket, guild_id: int):
            await ws_manager.connect(websocket, guild_id)
            try:
                while True:
                    await websocket.receive_text()
            except WebSocketDisconnect:
                ws_manager.disconnect(websocket, guild_id)
            except Exception:
                ws_manager.disconnect(websocket, guild_id)
