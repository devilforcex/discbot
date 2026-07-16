# DiscBot — единен план и архив

Този файл заменя старите разпилени planning/report файлове в root директорията.
Целта е root да остане чист: `README.md`, 1–2 Windows launch/install файла и реалният код.

## 1. Активна цел

DiscBot е native Windows Discord music bot, заключен към:

```text
E:\discbot
```

Всичко свързано с бота трябва да е там:

- source code
- `.venv`
- `.env`
- `application.yml`
- `Lavalink.jar`
- `data/`
- `logs/`
- локален `ytcookies.txt`, ако се използва

Docker/Compose/Linux артефактите са премахнати от активния build.

## 2. Какво беше обединено

Старите файлове бяха:

- `implementation_plan.md` — исторически план за prefix commands, whitelist/blacklist, 24/7 режим.
- `IMPROVEMENT_PLAN.md` — phase план за UX, dashboard, player controls, tests, packaging.
- `OPTIMIZATION_REPORT.md` — доклад за refactor split на cogs/views/embeds/services.
- `WINDOWS_DEBUG_OPTIMIZATION_PLAN.md` — Windows debug checklist и native packaging бележки.

Те вече са обединени като резюме тук, за да няма 4–5 plan файла в root.

## 3. Изпълнено

### Backend / bot

- Prefix commands с `!`.
- Guild/channel restriction.
- Owner, whitelist, blacklist, access requests.
- SQLite persistence.
- Lavalink reconnect task.
- Music queue, loop, autoplay toggle, volume persistence.
- Favorites and playlists.
- Player controller за общи действия от commands/buttons/dashboard.

### Refactor / optimization

- Admin cogs са разделени по домейни.
- Music cogs са разделени на playback/queue/filters/library/utility.
- Embed logic е разделена в `bot/music/embeds/`.
- Views са разделени в `bot/music/views/`.
- Shared auth/voice/playback services са в `bot/core/services/`.
- Queue manager има unit tests.

### Dashboard

- FastAPI dashboard със status, Lavalink, now playing, queue, settings, stats, favorites/playlists.
- Bearer token защита за write actions.
- Dashboard route tests.
- **React SPA** (`web/`) — пълен replace на Jinja2 templates с React 19 + TypeScript + Vite + Tailwind v4.
  - Страници: Landing, Dashboard, Player, Statistics, Library (Favorites + Playlists), Settings, 404.
  - WebSocket real-time updates (`/ws/{guild_id}`) с auto-reconnect.
  - Toast notifications, ErrorBoundary, ProtectedRoute за auth.
  - TanStack Query polling (3-30s), Zustand auth state в localStorage.
  - SPA catch-all в `dashboard.py` за production serving.

### Windows packaging

- `install.ps1`, `setup.bat`, `start.ps1/.bat`, `stop.ps1/.bat`, `update.ps1/.bat`.
- Root wrappers: `install.bat`, `start.bat`.
- Inno Setup script: `scripts/windows/DiscBot.iss`.
- Fixed path enforcement: `E:\discbot` only.
- Lavalink config uses the YouTube source plugin and keeps built-in YouTube disabled.
- Optional cookies use `E:\discbot\ytcookies.txt` plus `plugins.youtube.cookieFile` in `application.yml`.

## 4. Активен debug checklist

```powershell
cd E:\discbot
.\.venv\Scripts\python.exe -m compileall -q bot tests
.\.venv\Scripts\python.exe -m unittest discover -v
.\.venv\Scripts\python.exe -m pip check
java -version
```

Lavalink отделно:

```powershell
cd E:\discbot
java -jar Lavalink.jar
```

Bot отделно:

```powershell
cd E:\discbot
.\.venv\Scripts\python.exe -m bot.main
```

## 5. Текущи приоритети

1. ~~Live test на `!play` с реален Lavalink/Discord token.~~ ✅
2. ~~Проверка на player embed съобщението след `!play` и `!nowplaying`.~~ ✅
3. ~~Проверка на help menu dropdown/buttons.~~ ✅
4. ~~Проверка на Windows installer от чиста машина.~~ ✅
5. ~~Ако YouTube блокира — локален `ytcookies.txt`, uncomment `youtube.cookieFile` в `application.yml`.~~ ✅
6. React SPA dashboard — ✅ завършен (6 phases).
7. WebSocket real-time updates — ✅ завършен.
8. Library management (favorites + playlists) в SPA — ✅ завършен.

## 6. Правило за бъдещи планове

- Не добавяме нов root `*_PLAN.md` / `*_REPORT.md` файлове.
- Новите бележки се добавят тук или в `docs/`.
- `README.md` остава кратък operational guide, не исторически архив.
