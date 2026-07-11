# 🎵 Discord Music Bot

A production-ready private Discord music bot with **Lavalink v4** audio backend, **SQLite** persistence, and an optional **FastAPI** web dashboard. Designed for smooth music playback inspired by boogie.gg.

## ✨ Features

- **20+ Prefix Commands** — Full music playback control using `!` prefix
- **Lavalink v4** — High-quality audio streaming via Wavelink v3
- **YouTube & Spotify** — URL support and keyword search
- **Queue Management** — Add, remove, shuffle, loop (track/queue)
- **Autoplay** — Automatic recommendations when queue is empty
- **Volume Control** — Per-guild volume persistence
- **Interactive Embed Player** — Persistent Now Playing message with working buttons (pause, skip, stop, shuffle, loop, volume, favorite, queue)
- **Rich Embeds** — Progress bar, status line, paginated queue, updated help menu
- **Web Dashboard** — Nightmare-style glass UI (FastAPI) + static landing in `docs/`- **Favorites System** — Save and manage favorite tracks per user
- **Playlists** — Create, manage, and play user-created playlists
- **Playback History** — Track listening statistics
- **Persistent Storage** — SQLite database for all settings and data
- **Web Dashboard** — Optional FastAPI dashboard for monitoring (REST API + HTML)
- **Error Handling** — Comprehensive error hierarchy with user-friendly messages
- **Structured Logging** — Rotating file + console output
- **Auto-Disconnect** — Leaves voice channel when alone

## 🏗️ Architecture

```
discbot/
├── bot/
│   ├── cogs/
│   │   ├── music_commands.py    # 14 music prefix command handlers
│   │   ├── admin_commands.py    # Access control & owner commands
│   │   └── events.py            # Guild join/leave, voice state tracking
│   ├── core/
│   │   ├── bot.py               # Bot subclass with lifecycle management
│   │   ├── errors.py            # Error hierarchy & global handler
│   │   └── logging_setup.py     # Rotating file + console logging
│   ├── database/
│   │   ├── database.py          # SQLite connection & table creation
│   │   ├── favorites_manager.py # Favorites CRUD operations
│   │   ├── guild_settings.py    # Per-guild configuration
│   │   ├── history_manager.py   # Playback history & statistics
│   │   └── playlist_manager.py  # Playlist CRUD operations
│   ├── music/
│   │   ├── embed_manager.py     # Rich embed builders (player + help)
│   │   ├── emoji.py             # Shared emoji + accent colors
│   │   ├── player_controller.py # Shared actions (commands + buttons)
│   │   ├── player_view.py       # Discord UI buttons (persistent)
│   │   ├── player_message.py    # Persistent Now Playing message
│   │   ├── lavalink_client.py   # Wavelink node management & events
│   │   ├── player.py            # Custom Wavelink Player with volume/autoplay
│   │   └── queue_manager.py     # Per-guild queue with loop/shuffle
│   ├── dashboard/
│   │   ├── dashboard.py         # FastAPI API + control endpoints
│   │   ├── templates/           # Nightmare glass UI
│   │   └── static/              # CSS / JS assets
│   ├── config.py                # pydantic-settings configuration
│   └── main.py                  # Entry point
├── .env.example                 # Environment variable template
├── application.yml.example      # Lavalink configuration template
├── requirements.txt             # Python dependencies
└── README.md
```

### Data Flow

1. **User** sends a prefix command (e.g., `!play`) → `discord.py` processes message
2. **MusicCommands cog** processes the command, validates voice state
3. If playing music: **Wavelink** queries **Lavalink** for audio stream
4. **Lavalink** streams audio to Discord voice channel
5. Queue state tracked in **QueueManager** (in-memory per guild)
6. Persistent data (favorites, playlists, settings) stored in **SQLite**
7. Optional **FastAPI dashboard** provides HTTP access to status/queue/settings

## 🛠️ Prerequisites

| Dependency | Version | Purpose |
|-----------|---------|---------|
| Python | 3.12+ | Runtime |
| Java | 17+ | Lavalink server |
| Lavalink | v4 | Audio streaming backend |
| Discord Bot Token | - | Discord API access |

## 🔧 Setup

### 1. Clone and Prepare

```bash
git clone https://github.com/devilforcex/discbot.git
cd discbot
```

### 2. Discord Developer Portal Setup

1. Go to [Discord Developer Portal](https://discord.com/developers/applications)
2. Create a **New Application**
3. Go to **Bot** → **Add Bot**
4. Under **Bot Permissions**, enable:
   - `Send Messages`
   - `Embed Links`
   - `Read Messages`
   - `Connect` (Voice)
   - `Speak` (Voice)
   - `Use Voice Activity`
5. Copy the **Token** — this is your `DISCORD_BOT_TOKEN`
6. Go to **OAuth2** → **URL Generator**
   - Scopes: `bot`, `applications.commands`
   - Permissions: as above
   - Use the generated URL to invite the bot to your server

### 3. Environment Variables

```bash
cp .env.example .env
```

Edit `.env` and set at minimum:

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `DISCORD_BOT_TOKEN` | ✅ | - | Your bot token from Discord Developer Portal |
| `GUILD_ID` | ✅ | - | Discord guild ID the bot is restricted to |
| `MUSIC_CHANNEL_ID` | ✅ | - | Channel ID where music commands are allowed |
| `OWNER_ID` | ✅ | - | Bot owner (super-admin, bypasses all checks) |
| `LAVALINK_HOST` | ✅ | 127.0.0.1 | Lavalink server host |
| `LAVALINK_PORT` | ✅ | 12333 | Lavalink server port |
| `LAVALINK_PASSWORD` | ✅ | youshallnotpass | Lavalink server password |
| `SPOTIFY_CLIENT_ID` | ❌ | - | For Spotify URL support |
| `SPOTIFY_CLIENT_SECRET` | ❌ | - | For Spotify URL support |
| `DATABASE_PATH` | ❌ | data/musicbot.db | Path to SQLite database |
| `LOG_LEVEL` | ❌ | INFO | Logging level |
| `DASHBOARD_ENABLED` | ❌ | false | Enable web dashboard |

### 4. Lavalink Setup

1. Download **Lavalink v4** from [GitHub Releases](https://github.com/lavalink-devs/Lavalink/releases)
2. Place the `Lavalink.jar` in the project root (or any directory)
3. Copy the application config:
    ```bash
    cp application.yml.example application.yml
    ```
4. Edit `application.yml` to match your `.env` settings
5. (Optional) For Spotify support:
    - Register an app at [Spotify Developer Dashboard](https://developer.spotify.com/dashboard)
    - Get `Client ID` and `Client Secret`
    - Download the [LavaSpotify plugin](https://github.com/lavalink-devs/lava-spotify)
    - Place the plugin jar in a `plugins/` folder next to Lavalink.jar
    - Uncomment the `plugins` section in `application.yml`

#### YouTube Cookies (Optional)

For age-restricted or region-locked YouTube videos, you can use cookies:

1. **Using Docker Compose** (recommended):
   - The `ytcookies.txt` file in the project root is automatically mounted to the Lavalink container
   - Ensure `cookieFile` is configured in `docker/lavalink/application.yml` (already done)

2. **Local Lavalink setup**:
   - Place `ytcookies.txt` in the same directory as your `application.yml`
   - Add to `application.yml`:
     ```yaml
     lavalink:
       server:
         youtube:
           cookieFile: "ytcookies.txt"
     ```

3. **Exporting cookies from your browser**:
   - Install a browser extension like "Get cookies.txt LOCALLY" (Chrome) or "cookies.txt" (Firefox)
   - Log into YouTube in your browser
   - Export cookies to `ytcookies.txt` in Netscape format

### 5. Python Dependencies

```bash
pip install -r requirements.txt
```

This installs:
- `discord.py>=2.4.0` — Discord API
- `wavelink>=3.0.0` — Lavalink v4 client
- `fastapi>=0.111.0` — Web dashboard (optional)
- `uvicorn[standard]>=0.30.0` — ASGI server (optional)
- `pydantic>=2.7.0` — Configuration validation
- `pydantic-settings>=2.3.0` — .env loading
- `python-dotenv>=1.0.0` — .env file parsing
- `aiofiles>=24.1.0` — Async file ops (dashboard)
- `jinja2>=3.1.0` — Template engine (dashboard)
- `python-multipart>=0.0.9` — Form parsing (dashboard)

### 6. Run the Bot

Ensure Lavalink is running first, then:

```bash
python bot/main.py
```

### 7. Development Checks

Run the lightweight stdlib test suite before production changes:

```bash
python -m unittest discover -v
```

Static syntax check:

```bash
python -m compileall -q bot tests
```

### 8. Docker Compose Deployment

The repository includes a Compose stack for the bot and Lavalink:

```bash
cp .env.example .env
# edit .env: DISCORD_BOT_TOKEN, GUILD_ID, MUSIC_CHANNEL_ID, OWNER_ID, etc.
docker compose up -d --build
docker compose logs -f bot
```

Services:

| Service | Purpose | Notes |
|---------|---------|-------|
| `bot` | Python Discord bot | Uses `.env`, stores SQLite under `./data` |
| `lavalink` | Lavalink v4 audio backend | Config: `docker/lavalink/application.yml` |

Compose overrides `LAVALINK_HOST=lavalink` because containers talk over the internal Docker network. Keep `LAVALINK_PASSWORD` in `.env` matched with `docker/lavalink/application.yml`.

Useful commands:

```bash
docker compose ps
docker compose logs -f lavalink
docker compose restart bot
docker compose down
```

### Updating an Existing Checkout

There is no need to delete and clone the repository again. From the existing
project directory, run:

```bash
./update.sh
```

The script safely fast-forwards the currently checked-out branch, pulls the
latest Lavalink image, and rebuilds/restarts the Compose stack. It preserves
ignored runtime files such as `.env`, `data/`, and `logs/`, and stops instead of
overwriting tracked local changes.

To update the source without restarting Docker:

```bash
./update.sh --pull-only
```

If the dashboard is enabled with `DASHBOARD_ENABLED=true`, it is exposed at `http://localhost:18080`.

## 📋 Commands

All commands use the `!` prefix.

### Playback
| Command | Description |
|---------|-------------|
| `!play <query>` (`!p`) | Search YouTube/Spotify or play from URL |
| `!pause` | Pause current playback |
| `!resume` | Resume paused playback |
| `!skip` (`!s`) | Skip to next track |
| `!stop` | Stop playback and clear queue |
| `!disconnect` (`!dc`) | Disconnect from voice channel |
| `!nowplaying` (`!np`) | Refresh persistent player + buttons |

### Queue
| Command | Description |
|---------|-------------|
| `!queue [page]` (`!q`) | View the current queue |
| `!shuffle` | Shuffle the queue |
| `!loop <none\|track\|queue>` | Set loop mode |
| `!autoplay [on\|off\|toggle]` | Toggle automatic recommendations |

### Settings
| Command | Description |
|---------|-------------|
| `!volume <0-100>` (`!vol`) | Set playback volume |
| `!ping` | Check bot and Lavalink latency |
| `!help` | Show all commands + player button legend |

### Player buttons (on Now Playing message)

| Button | Action |
|--------|--------|
| ⏯️ | Pause / resume |
| ⏭️ | Skip |
| ⏹️ | Stop + clear queue |
| 🔀 | Shuffle queue |
| 🔁 | Cycle loop (none → track → queue) |
| 🔉 / 🔊 | Volume −10 / +10 |
| ⭐ | Favorite current track |
| 📋 | Ephemeral queue view |
| 🔌 | Disconnect from voice |

Buttons require whitelist (or owner). User should be in the same voice channel for transport controls.

### User Info
| Command | Description |
|---------|-------------|
| `!whoami` | Show your user ID, access status, guild, and channel |
| `!status` | Show bot status and Lavalink info |

### Favorites
| Command | Description |
|---------|-------------|
| `!favorite` | Save current track |
| `!favorites [page]` | List saved favorites |

### Playlists
| Command | Description |
|---------|-------------|
| `!playlist_create <name> [description]` | Create a playlist |
| `!playlist_add <playlist_id>` | Add current track to playlist |
| `!playlist_remove <playlist_id> <position>` | Remove track from playlist |
| `!playlist_play <playlist_id>` | Queue all tracks from playlist |

### Owner Commands
| Command | Description |
|---------|-------------|
| `!adduser <id/mention>` | Add a user to the whitelist |
| `!removeuser <id/mention>` | Remove a user from the whitelist |
| `!listusers` | List all approved users |
| `!approve <id/mention>` | Approve an access request |
| `!deny <id/mention>` | Deny an access request |
| `!pendingrequests` | Show pending access requests |
| `!blacklist <id/mention>` | Blacklist a user |
| `!unblacklist <id/mention>` | Remove a user from blacklist |
| `!247 <on/off>` | Toggle 24/7 mode |

### Public Commands
| Command | Description |
|---------|-------------|
| `!requestaccess` | Submit an access request to the owner |
| `!whoami` | Show your user info and access status |
| `!status` | Display bot status |

## 🔒 Access Control

The bot uses a local access control system with SQLite persistence. All IDs are configured in `.env` and `config.py` — never hardcoded.

### Bot Owner
- The Discord user configured as `OWNER_ID` in `.env` is treated as the bot owner
- The owner **bypasses all permission checks** including blacklist
- Only the owner can use whitelist, blacklist, approve, deny, and 24/7 commands

### Whitelist (Approved Users)
- Users must be added by the owner using `!adduser <id_or_mention>`
- Approved users can use all music commands
- The list persists across bot restarts in SQLite's `approved_users` table

### Blacklist
- Blacklisted users are blocked from all bot commands
- Blacklist **overrides** whitelist — even approved users can be blacklisted
- Managed via `!blacklist <id/mention>` and `!unblacklist <id/mention>` by the owner

### Access Requests
- Unauthorized users can submit a request via `!requestaccess`
- The request is stored in the `access_requests` table with username, display name, guild, and timestamp
- The owner is notified via DM
- The owner can then use `!approve <id/mention>` or `!deny <id/mention>`

### Authorization Check Order
1. **Owner** — Always passes
2. **Blacklist** — Blocked with "❌ You are blacklisted."
3. **Whitelist** — Passes if found in approved users
4. **Deny** — "❌ You are not authorized to use this bot."

## 🏠 Server Restriction

The bot only responds to commands in the Discord server configured as `GUILD_ID` in `.env`. Commands from other servers are silently ignored.

## 🎵 Music Channel Restriction

Music commands can only be used in the channel configured as `MUSIC_CHANNEL_ID` in `.env`. Using a music command elsewhere returns:

> ❌ Music commands may only be used in the designated music channel.

The following commands are **exempt** from this restriction and work anywhere:
- `!help`
- `!ping`
- `!whoami`
- `!requestaccess`

## 🔄 24/7 Mode

When enabled, the bot automatically reconnects after a restart and returns to the configured voice channel.

### Available Commands
| Command | Description |
|---------|-------------|
| `!247 on` | Enable 24/7 mode (owner only) |
| `!247 off` | Disable 24/7 mode (owner only) |

The setting is persisted in the `bot_settings` SQLite table and survives bot restarts.

## 🔧 Auto-Recovery

### Lavalink Reconnection
If the Lavalink server disconnects, the bot automatically retries the connection using **exponential backoff**:

1. Attempt 1: 1 second delay
2. Attempt 2: 2 second delay
3. Attempt 3: 4 second delay
4. Attempt 4: 8 second delay
5. Attempt 5+: 16–60 second delay (capped at 60s)

All reconnection failures are logged.

## 🌐 Web Dashboard

The dashboard is **optional** and **isolated**. Enable it by setting:

```env
DASHBOARD_ENABLED=true
DASHBOARD_HOST=127.0.0.1
DASHBOARD_PORT=18080
```

### API Endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /` | HTML status page |
| `GET /api/status` | Bot status (JSON) |
| `GET /api/lavalink` | Lavalink status (JSON) |
| `GET /api/queue/{guild_id}` | Queue contents (JSON) |
| `GET /api/nowplaying/{guild_id}` | Current track (JSON) |
| `GET /api/stats/{guild_id}` | Playback statistics (JSON) |
| `GET /api/settings/{guild_id}` | Guild settings (JSON) |
| `POST /api/settings/{guild_id}` | Update guild settings (JSON) |
| `GET /api/favorites/{user_id}` | User favorites (JSON) |
| `GET /api/playlists/{user_id}` | User playlists (JSON) |

## 🗄️ Database

The bot uses **SQLite** for persistent storage. Database file location is configured via `DATABASE_PATH` in `.env` (default: `data/musicbot.db`).

### Tables
- `guild_settings` — Per-guild volume, autoplay, announce preferences
- `user_favorites` — User-saved tracks (unique per user+track)
- `playlists` — User-created playlists with UUID identifiers
- `playlist_tracks` — Tracks within playlists (ordered by position)
- `playback_history` — Log of all played tracks for statistics
- `approved_users` — Whitelist of authorized users (user_id, username, display_name, added_by)
- `access_requests` — Self-registration requests (status: pending/approved/denied)
- `blacklisted_users` — Blacklisted users (overrides whitelist)
- `audit_logs` — Security audit log (action, target, moderator, timestamp)
- `bot_settings` — Key-value store (24/7 mode state, etc.)

### Backups

To backup your database:
```bash
copy data\musicbot.db data\musicbot_backup.db
```

## 🚀 Deployment

### Production Considerations

1. **Use a process manager** like systemd or PM2 to keep the bot running
2. **Run Lavalink as a service** with auto-restart
3. **Set up logging** — Logs rotate automatically at 10MB (5 backups)
4. **Dashboard** — Keep bound to `127.0.0.1` or use a reverse proxy with auth
5. **Database** — Set up periodic backups

### Windows (easy mode)

Ботът живее в **`E:\discbot`** — всичко се инсталира и работи само там
(код, `.venv`, `Lavalink.jar`, `.env`, `data/`, `logs/`).

Отвори **PowerShell** (Win+R → `powershell`) и постави един ред:

```powershell
# 🚀 ПЪРВА ИНСТАЛАЦИЯ — сваля и инсталира всичко в E:\discbot
irm https://raw.githubusercontent.com/devilforcex/discbot/master/scripts/windows/install.ps1 | iex

# ⬆️ ЪПДЕЙТ — сваля нов код в E:\discbot и рестартира бота
irm https://raw.githubusercontent.com/devilforcex/discbot/master/scripts/windows/update.ps1 | iex

# Force update when you have stray tracked edits (keeps .env / data / untracked)
$env:DISCBOT_FORCE = '1'
irm https://raw.githubusercontent.com/devilforcex/discbot/master/scripts/windows/update.ps1 | iex
```

> Ако искаш друга папка, сетни променлива преди one-liner-а:
> ```powershell
> $env:DISCBOT_DIR = 'D:\my-stuff\discbot'
> ```

Инсталаторът ще (всичко в `E:\discbot`):
- клонира repo-то
- провери/отвори download страниците за Python 3.12+ и Java 17+
- създаде `.venv` и инсталира pip зависимостите
- направи `.env` и `application.yml` от шаблоните и отвори `.env` за редакция
- свали автоматично последния `Lavalink.jar`
- по желание стартира бота веднага

Алтернативно (без PowerShell one-liner):
1. Клонирай/разархивирай repo-то в `E:\discbot`
2. Двойно кликни `E:\discbot\scripts\windows\setup.bat`
3. Попълни `DISCORD_BOT_TOKEN`, `GUILD_ID`, `MUSIC_CHANNEL_ID`, `OWNER_ID` в `.env`
4. Двойно кликни `E:\discbot\scripts\windows\start.bat`

Помощни скриптове в `scripts\windows\`:
| Файл | Какво прави |
|------|-------------|
| `install.ps1` | PowerShell one-liner инсталатор (`irm ... \| iex`) |
| `update.ps1` | PowerShell one-liner ъпдейтър (`irm ... \| iex`) |
| `setup.bat` | Първоначална инсталация с batch |
| `start.bat` / `start.ps1` | Стартират Lavalink и бота в отделни прозорци |
| `stop.bat` / `stop.ps1` | Спират двата процеса |
| `update.bat` | `git pull` + обновяване на pip пакетите (batch) |
| `DiscBot.iss` | Inno Setup скрипт за компилиране на `DiscBotSetup.exe` |
| `README-windows.md` | Пълно ръководство + често срещани проблеми |

> 💡 Ако `irm | iex` ти гърми с "execution of scripts is disabled", пусни веднъж:
> `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` и отговори `Y`.

#### Windows (като сервиз)

За автостарт при boot ползвай `nssm` или сложи shortcut на `start.bat`/`start.ps1` в
`shell:startup`. С `nssm` (пример с инсталация в `E:\discbot`):
```bash
nssm install DiscBot "E:\discbot\.venv\Scripts\python.exe" "E:\discbot\bot\main.py"
nssm set DiscBot AppDirectory "E:\discbot"
nssm set DiscBot Start SERVICE_AUTO_START
nssm start DiscBot
```

### Linux (systemd)

```ini
[Unit]
Description=Discord Music Bot
After=network.target

[Service]
Type=simple
User=discbot
WorkingDirectory=/opt/discbot
ExecStart=/usr/bin/python3 /opt/discbot/bot/main.py
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
```

## 🔍 Troubleshooting

### Bot doesn't respond to prefix commands
- Ensure `message_content` intent is enabled in Discord Developer Portal
- Ensure the bot is in the correct guild (check `GUILD_ID` in `.env`)
- Ensure you are in the correct channel (check `MUSIC_CHANNEL_ID` in `.env`)
- Verify you are authorized: use `!whoami` to check your access status
- If unauthorized, use `!requestaccess` to submit a request to the owner
- Check that the command prefix `!` is being used

### "Lavalink not connected" error
- Ensure Lavalink is running: `java -jar Lavalink.jar`
- Check `application.yml` password matches `.env`
- Verify port `12333` is not blocked by firewall
- Check Lavalink logs for errors

### No audio playback
- Ensure bot has `Connect` and `Speak` permissions in voice channel
- Check Lavalink sources in `application.yml` (youtube: true)
- Verify Lavalink has internet access for YouTube streaming

### "Failed to Load Tracks" or "Something went wrong while looking up the track" errors
- **YouTube is blocking requests** - Refresh your `ytcookies.txt` file with fresh cookies from an actively logged-in browser
- Check that cookies include: `VISITOR_INFO_LIVE`, `SID`, `__Secure-1PSID`, `LOGIN_INFO`
- Ensure the cookies file is in **Netscape format** (not JSON)
- For Docker: verify volume mount is correct (`./ytcookies.txt:/opt/Lavalink/ytcookies.txt:ro`)
- Try a different, non-age-restricted video to confirm the issue
- Check Lavalink logs: `docker compose logs -f lavalink` for detailed error messages

### "Track not found" errors
- YouTube may be rate-limiting — try again later
- For Spotify URLs, ensure Spotify plugin is installed in Lavalink

### Dashboard not working
- Install dashboard dependencies: `pip install fastapi uvicorn jinja2 aiofiles python-multipart`
- Ensure `DASHBOARD_ENABLED=true` in `.env`
- Check port `18080` is not in use

### Database errors
- Ensure the `data/` directory exists (created automatically)
- Check file permissions on `data/musicbot.db`
- For corruption: delete the database file (data will be lost) and restart

## 📄 License

This project is private. All rights reserved.

## 🤝 Support

For issues, please open a GitHub issue at:
https://github.com/devilforcex/discbot/issues