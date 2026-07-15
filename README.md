# 🎵 DiscBot — Windows Discord Music Bot

Private Discord music bot за Windows с Lavalink v4, SQLite база, persistent embed player с бутони и optional FastAPI dashboard.

> **Важно:** този build е заключен към **`E:\discbot`**. Всички файлове на бота стоят само там: код, `.venv`, `.env`, `application.yml`, `Lavalink.jar`, `data/`, `logs/` и локален `ytcookies.txt`.

## 🚀 Най-бърз старт

### 1) Първа инсталация

Отвори PowerShell и пусни:

```powershell
irm https://raw.githubusercontent.com/devilforcex/discbot/master/scripts/windows/install.ps1 | iex
```

Или ако вече имаш repo-то разархивирано/клонирано, double-click:

```text
install.bat
```

Инсталаторът:

- създава/използва `E:\discbot`
- клонира repo-то там
- проверява Python 3.12+ и Java 17+
- създава `.venv`
- инсталира `requirements.txt`
- копира `.env.example` → `.env`
- копира `application.yml.example` → `application.yml` с включен YouTube source plugin
- сваля `Lavalink.jar`
- отваря `.env` за попълване

### 2) Попълни `.env`

Минимум:

```env
DISCORD_BOT_TOKEN=your_token
GUILD_ID=your_server_id
MUSIC_CHANNEL_ID=your_music_text_channel_id
OWNER_ID=your_discord_user_id
LAVALINK_HOST=127.0.0.1
LAVALINK_PORT=12333
LAVALINK_PASSWORD=youshallnotpass
```

В Discord Developer Portal включи **Message Content Intent**.

### 3) Стартиране

Double-click:

```text
start.bat
```

или:

```powershell
powershell -ExecutionPolicy Bypass -File E:\discbot\scripts\windows\start.ps1
```

Ще се отворят два прозореца:

1. Lavalink
2. Discord bot

### 4) Спиране

```powershell
powershell -ExecutionPolicy Bypass -File E:\discbot\scripts\windows\stop.ps1
```

### 5) Update

```powershell
irm https://raw.githubusercontent.com/devilforcex/discbot/master/scripts/windows/update.ps1 | iex
```

## 📁 Важни файлове

| Path | За какво е |
|---|---|
| `E:\discbot\.env` | Discord token, IDs, dashboard settings |
| `E:\discbot\application.yml` | Lavalink config |
| `E:\discbot\Lavalink.jar` | Lavalink server |
| `E:\discbot\data\musicbot.db` | SQLite база |
| `E:\discbot\logs\` | Bot logs |
| `E:\discbot\scripts\windows\` | Windows install/start/stop/update scripts |
| `docs\PROJECT_PLAN.md` | Единен план + архив на старите планове |

## 🎮 Основни команди

Всички команди са с prefix `!`.

### Playback

| Command | Описание |
|---|---|
| `!play <song/url>` / `!p` | Търси и пуска песен |
| `!pause` | Pause |
| `!resume` | Resume |
| `!skip` / `!s` | Skip |
| `!stop` | Stop + clear queue |
| `!disconnect` / `!dc` | Изкарва бота от voice |
| `!nowplaying` / `!np` | Показва/обновява embed player-а |

### Queue / player

| Command | Описание |
|---|---|
| `!queue` / `!q` | Показва queue |
| `!shuffle` | Shuffle |
| `!loop none/track/queue` | Loop mode |
| `!autoplay on/off/toggle` | Autoplay |
| `!volume 0-100` / `!vol` | Volume |

### Library

| Command | Описание |
|---|---|
| `!favorite` / `!fav` | Запазва текущата песен |
| `!favorites` | Показва favorites |
| `!playlist_create <name>` | Създава playlist |
| `!playlists` | Показва playlists |
| `!playlist_add <id>` | Добавя текущата песен |
| `!playlist_play <id>` | Пуска playlist |

### Access / admin

| Command | Описание |
|---|---|
| `!requestaccess` | Заявка за достъп |
| `!whoami` | Показва ID/access status |
| `!status` | Bot/Lavalink status |
| `!adduser <id/@user>` | Owner: whitelist |
| `!removeuser <id/@user>` | Owner: remove whitelist |
| `!approve <id/@user>` | Owner: approve request |
| `!deny <id/@user>` | Owner: deny request |
| `!blacklist <id/@user>` | Owner: blacklist |
| `!247 on/off` | Owner: 24/7 mode |

## 🕹️ Embed player

`!nowplaying` / `!np` създава persistent player message в music channel-а.

Бутони:

- ⏯ pause/resume
- ⏭ skip
- ⏹ stop
- 🔀 shuffle
- 🔁 loop
- 🔉 / 🔊 volume
- ⭐ favorite
- 📋 queue
- 🔌 disconnect
- 🎛️ filter dropdown

Ако player embed-ът не се появи:

1. Провери bot permissions: `Send Messages`, `Embed Links`, `Use External Emojis`, `Read Message History`.
2. Пусни `!np` в правилния `MUSIC_CHANNEL_ID` канал.
3. Провери дали ботът има достъп до този text channel.
4. Виж `logs\discbot.log`.

## 🌐 Dashboard optional

В `.env`:

```env
DASHBOARD_ENABLED=true
DASHBOARD_HOST=127.0.0.1
DASHBOARD_PORT=18080
DASHBOARD_SECRET_KEY=long_random_secret
```

Отвори:

```text
http://127.0.0.1:18080
```

Write actions искат Bearer token = `DASHBOARD_SECRET_KEY`.

## 🍪 YouTube cookies optional

Ако YouTube блокира заявки или има age/region restriction:

1. Export cookies в Netscape format като `ytcookies.txt`.
2. Сложи файла в `E:\discbot\ytcookies.txt`.
3. В `application.yml` uncomment-ни:

```yaml
plugins:
  youtube:
    cookieFile: "ytcookies.txt"
```

4. Restart Lavalink + bot.

## 🧪 Debug checks

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

## 🔧 Чести проблеми

### Ботът влиза във voice, но не пуска музика

Провери в този ред:

1. Lavalink прозорецът има ли грешка при loading track?
2. `.env` `LAVALINK_PASSWORD` съвпада ли с `application.yml` password?
3. В `application.yml` Spotify plugin да не е включен с fake credentials.
4. Пробвай директен YouTube URL, не само search query.
5. Ако YouTube блокира — добави fresh `ytcookies.txt`.
6. Пусни `!ping` — трябва да показва Lavalink Connected.

### `!play` не реагира

- Message Content Intent трябва да е ON.
- Командата трябва да е в `MUSIC_CHANNEL_ID`.
- Потребителят трябва да е whitelist-нат или owner.
- Провери `!whoami`.

### Help менюто няма dropdown/buttons

- Ботът трябва да има permission `Use External Emojis` и `Embed Links`.
- Discord client понякога cache-ва — пробвай reload.
- Провери дали bot process няма exception в logs.

## 🚄 Railway deployment (cloud)

DiscBot може да се хоства на **Railway** — Lavalink + Python бот в един контейнер, с PostgreSQL база, CI/CD от GitHub и автоматично деплойване.

### Какво включва

- **Docker multi-stage build**: Java 17 (Lavalink) + Python 3.12 (бот) в един контейнер.
- **PostgreSQL поддръжка**: автоматично ползва PostgreSQL ако `DATABASE_URL` е зададена, иначе SQLite.
- **CI/CD**: GitHub Actions — тестове при всеки push (`test.yml`), автоматичен деплой в Railway при push към `master` (`deploy.yml`).
- **Автоматичен deploy скрипт** — `scripts/deploy/railway.sh` (Linux/Mac/Git Bash).

### Ръчен деплой стъпка по стъпка

1. **Инсталирай Railway CLI**:

   ```bash
   npm install -g @railway/cli
   ```

   или (Windows):

   ```powershell
   npm install -g @railway/cli
   ```

2. **Логни се**:

   ```bash
   railway login
   ```

3. **Създай проект** (еднократно):

   ```bash
   railway init
   ```

4. **Добави PostgreSQL**:

   ```bash
   railway add postgres
   ```

5. **Настрой environment variables**:

   ```bash
   railway env
   ```

   Минимум:
   ```
   DISCORD_BOT_TOKEN=your_bot_token
   GUILD_ID=your_guild_id
   MUSIC_CHANNEL_ID=your_music_channel_id
   OWNER_ID=your_discord_id
   DASHBOARD_ENABLED=true
   DASHBOARD_SECRET_KEY=your_secret_key
   ```

   `DATABASE_URL` се задава **автоматично** от PostgreSQL add-on-а.

6. **Деплой**:

   ```bash
   railway up
   ```

### Автоматичен GitHub Actions деплой

Когато `master` клонът получи нов commit, GitHub Actions автоматично:

1. Пуска тестовете (Python 3.12).
2. Ако тестовете минат, деплойва в Railway.

**За да работи**:

1. Отиди в Railway Dashboard → Project → Tokens → Generate token.
2. Копирай токена.
3. Отиди в GitHub → Settings → Secrets and variables → Actions → New secret.
4. Име: `RAILWAY_TOKEN`, стойност: копирания токен.

### Автоматичен deploy скрипт

```bash
bash scripts/deploy/railway.sh
```

Този скрипт:
- Проверява дали Railway CLI е инсталиран.
- Логва те в Railway (ако не сте логнати).
- Създава проект (ако нямате).
- Добавя PostgreSQL.
- Насочва `DATABASE_URL`, `DISCORD_BOT_TOKEN`, `GUILD_ID`, `MUSIC_CHANNEL_ID`, `OWNER_ID`, `DASHBOARD_SECRET_KEY` и `DASHBOARD_ENABLED=true`.
- Деплойва (`railway up`).

### Важно

- Railway използва `Dockerfile` от root-а на repo-то. Не е нужно да конфигурираш нищо допълнително — `railway.json` вече насочва към Dockerfile.
- Lavalink swap-ът и temp директориите са настроени в `docker-entrypoint.sh`.
- Healthcheck проверява Lavalink REST API на всеки 30 секунди.

## 🛠️ Developer checks

```bash
python -m compileall -q bot tests
python -m unittest discover -v
```

## Бележка

Нямам директен достъп до архивирани разговори извън текущия repo/context. Затова старите планове са консолидирани в `docs\PROJECT_PLAN.md`, а README вече е operational guide вместо исторически документ.
