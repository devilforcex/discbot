"""
FastAPI web dashboard — refactored slim server.

Routes moved to routes.py for maintainability.
Glassmorphic Nightmare Music UI + REST API.
"""
import logging
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)

try:
    from fastapi import FastAPI, HTTPException, Depends
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
    """Optional FastAPI web dashboard server."""

    def __init__(self, bot):
        self.bot = bot
        self._app = None
        self._server = None
        self._templates = None
        self._running = False

    async def start(self) -> None:
        if not HAS_FASTAPI:
            logger.warning("Dashboard dependencies not installed. Install: pip install fastapi uvicorn jinja2 aiofiles")
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
        logger.info("Dashboard available at http://%s:%s", config.dashboard_host, config.dashboard_port)
        await self._server.serve()

    async def stop(self) -> None:
        self._running = False
        if self._server:
            self._server.should_exit = True
            logger.info("Dashboard server stopped")

    def _check_write_auth(self, credentials: Optional[Any]) -> None:
        secret = getattr(self.bot.config, "dashboard_secret_key", "") or ""
        if not secret or secret == "change_me_to_a_random_secret_key":
            return
        if credentials is None or credentials.credentials != secret:
            from fastapi import HTTPException

            raise HTTPException(status_code=401, detail="Invalid or missing Bearer token")

    def _register_routes(self) -> None:
        app = self._app
        bot = self.bot
        templates = self._templates
        security = HTTPBearer(auto_error=False)

        # Delegate to split routes module
        try:
            from .routes import register_routes

            register_routes(app, bot, templates, security, self._check_write_auth)
        except ImportError as e:
            logger.error("Failed to load dashboard routes: %s", e)
            raise
