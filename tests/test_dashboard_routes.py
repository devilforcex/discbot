import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

try:
    from fastapi import FastAPI, HTTPException
    from fastapi.security import HTTPBearer
    from fastapi.testclient import TestClient
except Exception:  # pragma: no cover - optional dependency guard
    FastAPI = None

from bot.database import database as db


@unittest.skipIf(FastAPI is None, "FastAPI test dependencies are not installed")
class DashboardRoutesTests(unittest.TestCase):
    def setUp(self):
        from bot.dashboard.routes import register_routes

        self.tmp = tempfile.TemporaryDirectory()
        self.db_path = str(Path(self.tmp.name) / "dashboard.db")
        db.initialize_database(self.db_path)

        guild = SimpleNamespace(id=123, name="Arena Guild", member_count=7, icon=None)
        self.bot = SimpleNamespace(
            user=None,
            latency=0.042,
            guilds=[guild],
            voice_clients=[],
            config=SimpleNamespace(database_path=self.db_path),
            queue_manager=FakeQueueManager(),
            is_ready=lambda: True,
            get_guild=lambda guild_id: guild if guild_id == guild.id else None,
        )
        app = FastAPI()
        security = HTTPBearer(auto_error=False)

        def check_write_auth(credentials):
            if credentials is None or credentials.credentials != "secret":
                raise HTTPException(status_code=401, detail="Invalid or missing Bearer token")

        register_routes(app, self.bot, templates=None, security=security, check_write_auth=check_write_auth)
        self.client = TestClient(app)

    def tearDown(self):
        db.close_connection(self.db_path)
        self.tmp.cleanup()

    def test_guilds_and_overview_routes(self):
        guilds = self.client.get("/api/guilds")
        self.assertEqual(guilds.status_code, 200)
        self.assertEqual(guilds.json()["guilds"][0]["name"], "Arena Guild")

        overview = self.client.get("/api/overview/123")
        self.assertEqual(overview.status_code, 200)
        payload = overview.json()
        self.assertEqual(payload["guild"]["name"], "Arena Guild")
        self.assertEqual(payload["queue_length"], 1)
        self.assertEqual(payload["settings"]["volume"], 50)
        self.assertEqual(payload["stats"]["total_plays"], 0)

    def test_settings_update_requires_auth_and_validates_payload(self):
        unauth = self.client.post("/api/settings/123", json={"volume": 80})
        self.assertEqual(unauth.status_code, 401)

        invalid = self.client.post(
            "/api/settings/123",
            headers={"Authorization": "Bearer secret"},
            json={"default_source": "bad"},
        )
        self.assertEqual(invalid.status_code, 400)

        saved = self.client.post(
            "/api/settings/123",
            headers={"Authorization": "Bearer secret"},
            json={"volume": 150, "autoplay": "false", "announce_songs": "yes", "default_source": "scsearch"},
        )
        self.assertEqual(saved.status_code, 200)
        settings = saved.json()["settings"]
        self.assertEqual(settings["volume"], 100)
        self.assertEqual(settings["autoplay"], 0)
        self.assertEqual(settings["default_source"], "scsearch")


class FakeQueueManager:
    def get_all(self, guild_id):
        return [
            {
                "title": "Track",
                "author": "Artist",
                "uri": "https://example.invalid/track",
                "length": 123000,
                "requester_id": 1,
            }
        ]

    def get_length(self, guild_id):
        return len(self.get_all(guild_id))
