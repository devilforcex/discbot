# AGENTS.md — DiscBot

## Entrypoints

- **Bot**: `python -m bot.main` (calls `bot.core.bot.run_bot()`)
- **Dashboard (prod)**: bundled into bot process, FastAPI on `:18080`
- **Dashboard (dev frontend)**: `cd web && npm run dev` (Vite `:5173`, proxies `/api` → `:18080`)
- **Lavalink**: separate Java process — must run independently before starting the bot

## Quick commands

```bash
# Activate venv
.venv\Scripts\activate

# Run bot
python -m bot.main

# Run dashboard only (dev mode)
python -m bot.dashboard.dashboard

# Frontend build (required for production serving)
cd web && npm run build

# Tests (use project venv, not system python)
.venv\Scripts\python.exe -m pytest tests/ -x

# Lint / format Python
ruff check bot/
black bot/

# Typecheck
pyright
```

## Architecture

```
bot/
  main.py            # entry
  config.py          # pydantic-settings, loads .env
  core/bot.py        # discord.py Bot subclass
  music/             # Wavelink player, queue, search, lavalink client
  dashboard/
    dashboard.py     # FastAPI app, SPA catch-all from web/dist/
    routes.py        # all /api/* routes (register_routes(app, bot, security, check_write_auth))
    ws_manager.py    # WebSocket connection manager for real-time updates
  database/          # SQLAlchemy, SQLite/PostgreSQL via repository pattern

web/                 # React SPA (separate package.json, built → web/dist/)
```

## Key facts

- **No Docker** — runs locally via Python/Java processes
- **Python 3.11+**, no secrets committed (dashboard key in `.env`)
- **Frontend build artifacts** (`web/dist/`, `web/node_modules/`) are gitignored — must run `npm run build` before production serving
- **`register_routes()` signature**: `register_routes(app, bot, security, check_write_auth)`
- **Dashboard SPA catch-all** in `dashboard.py` serves `web/dist/` when directory exists; falls back to warning if not built
- **Lavalink**: downloads via `setup.py` or manually to `lavalink/Lavalink.jar` (v4, port `:12333`)
- **Config precedence**: `DATABASE_URL` (PostgreSQL) → falls back to `data/musicbot.db` (SQLite)
- **Tests use temp DB files** — fixture teardown cleans up; some PermissionError noise on Windows temp dirs is harmless

## API Endpoints

### Read (no auth required)
| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/health` | Bot health check |
| GET | `/api/health/lavalink` | Lavalink health check |
| GET | `/api/status` | Bot status (name, latency, guilds, uptime) |
| GET | `/api/guilds` | List guilds |
| GET | `/api/lavalink` | Lavalink connection status |
| GET | `/api/queue/{guild_id}` | Queue tracks |
| GET | `/api/nowplaying/{guild_id}` | Current track info |
| GET | `/api/stats/{guild_id}` | Playback statistics |
| GET | `/api/history/{guild_id}` | Recent playback history |
| GET | `/api/overview/{guild_id}` | Combined dashboard payload |
| GET | `/api/settings/{guild_id}` | Guild settings |
| GET | `/api/favorites/{user_id}` | User favorites (paginated) |
| GET | `/api/playlists/{user_id}` | User playlists |
| GET | `/api/playlists/{user_id}/{playlist_id}` | Playlist detail with tracks |

### Write (auth required — Bearer token)
| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/settings/{guild_id}` | Update guild settings |
| POST | `/api/control/{guild_id}/{action}` | Player controls (pause/resume/skip/stop/shuffle/volume) |
| POST | `/api/favorites/{user_id}` | Add favorite track |
| DELETE | `/api/favorites/{user_id}/{identifier}` | Remove favorite |
| POST | `/api/playlists/{user_id}` | Create playlist |
| DELETE | `/api/playlists/{playlist_id}` | Delete playlist |
| POST | `/api/playlists/{playlist_id}/tracks` | Add track to playlist |
| DELETE | `/api/playlists/{playlist_id}/tracks/{position}` | Remove track from playlist |

### WebSocket
| Protocol | Path | Description |
|----------|------|-------------|
| WS | `/ws/{guild_id}` | Real-time player state updates (now-playing, queue) |

## Auth

Simple Bearer token check against `DASHBOARD_SECRET_KEY` (shared secret, no JWT). Only write endpoints require auth. All `GET` endpoints are open. Config warns at startup if secret is still the default value.

## Frontend

React SPA with TanStack Query polling (3-30s intervals), Zustand for auth state (persisted to localStorage), Tailwind v4 CSS-first. WebSocket connection for real-time updates with automatic reconnection and exponential backoff. Toast notifications and error boundary for UX polish. Route protection redirects to landing page if no token set.

## Style / tooling

- Python: **ruff** (E/W/F/I/C4/UP/B/SIM, line-length 100, double quotes), **black**, **pyright** (basic mode, `reportMissingImports: false`)
- Frontend: **oxlint**, **TypeScript strict**, **Tailwind v4** (CSS-first, no `tailwind.config.js`)
- Line endings: repo uses LF; PowerShell converts to CRLF on checkout — warnings during `git add` are normal
