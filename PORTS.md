# DrusaBoT - Port Configuration & Access URLs

## Service Ports

| Service | Host | Port | Protocol | Description |
|---------|------|------|----------|-------------|
| **Discord Bot** | - | - | Gateway | Connects to Discord via WebSocket |
| **Dashboard (FastAPI)** | `0.0.0.0` | **18080** | HTTP | Web dashboard & REST API |
| **Lavalink** | `0.0.0.0` | **12333** | HTTP/WS | Audio streaming server |

## Access URLs (Local Development)

### Dashboard Web Interface
- **Landing Page**: `http://localhost:18080/`
- **Dashboard**: `http://localhost:18080/dashboard`
- **API Health**: `http://localhost:18080/api/health`
- **Bot Status**: `http://localhost:18080/api/status`
- **Lavalink Status**: `http://localhost:18080/api/lavalink`
- **Lavalink Health**: `http://localhost:18080/api/health/lavalink`

### Lavalink Direct Access
- **Info**: `http://localhost:12333/v4/info` (requires `Authorization: youshallnotpass`)
- **Version**: `http://localhost:12333/version`
- **Stats**: `http://localhost:12333/v4/stats` (requires auth)

## Environment Variables (`.env`)

```env
# Dashboard
DASHBOARD_ENABLED=true
DASHBOARD_HOST=0.0.0.0
DASHBOARD_PORT=18080
DASHBOARD_SECRET_KEY=your-secret-key-here
DASHBOARD_CORS_ORIGINS=http://localhost:18080,http://127.0.0.1:18080

# Lavalink
LAVALINK_HOST=127.0.0.1
LAVALINK_PORT=12333
LAVALINK_PASSWORD=youshallnotpass
LAVALINK_SECURE=false

# Discord
DISCORD_BOT_TOKEN=your-bot-token
GUILD_ID=1074037877899542538
MUSIC_CHANNEL_ID=1097945134630445227
MUSIC_VOICE_CHANNEL_ID=1097945134630445227
OWNER_ID=954887574248374322
```

## Startup Order

1. **Start Lavalink first** (port 12333)
   ```bash
   cd lavalink && java -jar Lavalink.jar
   ```
   Or use: `start_lavalink.bat`

2. **Start Discord Bot** (includes Dashboard on port 18080)
   ```bash
   python -m bot.main
   ```
   Or use: `start_bot.bat`

3. **Or start everything at once**:
   ```bash
   start_all.bat
   ```

## Shutdown

```bash
stop_all.bat
```

## Configuration Files

| File | Purpose |
|------|---------|
| `.env` | Main configuration (tokens, IDs, ports) |
| `lavalink/application.yml` | Lavalink server configuration |
| `bot/config.py` | Python config model (loads from .env) |

## Network Access

- **Dashboard** binds to `0.0.0.0:18080` - accessible from LAN
- **Lavalink** binds to `0.0.0.0:12333` - accessible from LAN
- For production behind reverse proxy, set `DASHBOARD_HOST=127.0.0.1`

## Health Checks

- `GET /api/health` - Returns `{ "ok": true, "ready": true }`
- `GET /api/health/lavalink` - Returns Lavalink connection status
- Lavalink: `GET /v4/info` with `Authorization` header

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Dashboard 500 error | Check `DASHBOARD_SECRET_KEY` is not default value |
| Lavalink connection failed | Verify Lavalink is running on port 12333 |
| Bot not responding | Check `DISCORD_BOT_TOKEN` in `.env` |
| Port already in use | Kill existing processes: `taskkill /F /IM python.exe /IM java.exe` |