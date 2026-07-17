# 🎵 DrusaBoT — Discord Music Bot

**DrusaBoT** е мощен Discord музикален бот, изграден с **discord.py 2.4+**, **Wavelink 3.0+ (Lavalink v4)**, **FastAPI dashboard** и поддръжка за **SQLite / PostgreSQL**.

> ⚠️ **Важно**: Този проект е за **локално стартиране** — няма Docker, няма контейнери. Просто стартираш Python скриптовете директно на твоя компютър.

---

## 📁 Структура на проекта

```
DrusaBoT/
├── bot/                          # Основен код на бота
│   ├── __init__.py
│   ├── main.py                   # 🎯 ТОЧКА НА СТАРТ — тук започва всичко
│   ├── config.py                 # ⚙️ Конфигурация (чреза .env)
│   ├── database/                 # 🗄️ Работа с база данни
│   │   ├── __init__.py
│   │   ├── connection.py         # SQLite / PostgreSQL пул за връзки
│   │   ├── models.py             # SQLAlchemy модели (Guild, User, Playlist, Settings)
│   │   └── repository.py         # CRUD операции (Repository pattern)
│   ├── music/                    # 🎵 Музикален плейър (ядрото)
│   │   ├── __init__.py
│   │   ├── player.py             # 🎮 Player — управление на плейъра, autoplay,(queue)
│   │   ├── queue_manager.py      # 📋 QueueManager — опашка с Playable обекти, лимит 500
│   │   ├── search.py             # 🔍 Търсене (YouTube, YouTube Music, SoundCloud)
│   │   ├── lavalink/             # 🔗 Връзка с Lavalink сървъра
│   │   │   ├── __init__.py
│   │   │   ├── client.py         # 🔌 LavalinkClient — връзка, health check, reconnect с backoff
│   │   │   ├── events.py         # 📡 Event handlers (track end, exception, node disconnect)
│   │   │   └── node.py           # ⚙️ Node конфигурация
│   │   └── commands/             # 🎮 Discord команди (slash commands)
│   │       ├── __init__.py
│   │       ├── playback.py       # /play, /pause, /resume, /stop, /skip, /seek
│   │       ├── queue_cmds.py     # /queue, /clear, /shuffle, /loop, /remove, /move
│   │       ├── playlist.py       # /playlist save/load/list/delete
│   │       ├── settings.py       # /settings (volume, source, autoplay, dj role)
│   │       └── admin.py          # /restart, /reload, /sync, /debug
│   ├── dashboard/                # 🌐 FastAPI Dashboard (Web UI)
│   │   ├── __init__.py
│   │   ├── dashboard.py          # 🚀 FastAPI app, CORS, auth middleware
│   │   ├── routes.py             # 🛣️ API рутове (/api/guilds, /api/settings, /api/health/lavalink)
│   │   ├── auth.py               # 🔐 JWT auth (HS256), login/logout, dependency injection
│   │   └── templates/            # 🎨 HTML шаблони (Jinja2)
│   │       ├── base.html
│   │       ├── login.html
│   │       ├── dashboard.html
│   │       └── guild_detail.html
│   └── utils/                    # 🛠️ Утилити
│       ├── __init__.py
│       ├── embeds.py             # 📦 Embed builders (unified style)
│       ├── formatters.py         # ⏱️ Форматиране на време, размер, прогрес бар
│       ├── permissions.py        # 🔐 Permission проверки (DJ role, admin, voice)
│       └── validators.py         # ✅ URL validation, volume clamp, source validation
├── tests/                        # 🧪 Тестове (pytest)
│   ├── __init__.py
│   ├── test_database.py
│   ├── test_queue_manager.py
│   ├── test_search_helpers.py
│   └── test_dashboard_routes.py
├── setup.py                      # 🛠️ Модерен инсталатор (интерактивно/auto, Lavalink download, start scripts)
├── start_bot.bat / start_bot.sh  # ▶️ Старт скриптове за бота
├── start_lavalink.bat / start_lavalink.sh  # ▶️ Старт скриптове за Lavalink
├── start_dashboard.bat / start_dashboard.sh  # ▶️ Старт скриптове за dashboard
├── .env.example                  # 📋 Примерен .env файл
├── requirements.txt              # 📦 Python зависимости
├── pytest.ini                   # ⚙️ pytest конфигурация
├── pyproject.toml               # ⚙️ Tooling config (ruff, black, pyright, mypy, pytest)
├── AGENTS.md                    # 🤖 Инструкции за AI агенти
└── README.md                    # 📖 Този файл
```

---

## 🚀 Бърз старт (Local Development) — Модерен инсталатор (препоръчително)

Най-лесния начин е чрез **`setup.py`** — той проверява пререквизити, създава виртуална среда, инсталира зависимости, изтегля Lavalink.jar, създава `.env` чрез интерактивен wizard и генерира старт скриптове.

```bash
# Клонирай репото
cd E:\DrusaBoT

# Интерактивен режим (препоръчително за първо стартиране)
python setup.py
```

Инсталаторът ще:
1. ✅ Провери **Python 3.11+**, **FFmpeg**, **Java 17+**, **Git**
2. 📦 Създаде `.venv` и инсталира зависимости от `requirements.txt`
3. 📥 Изтегли **Lavalink.jar** (последна стабилна версия)
4. ⚙️ Стартира **интерактивен wizard** за `.env` (токен, пароли, DB, dashboard)
5. 📝 Генерира старт скриптове: `start_bot.bat/.sh`, `start_lavalink.bat/.sh`, `start_dashboard.bat/.sh`

```bash
# Неинтерактивен режим (за CI/автоматизация)
python setup.py --non-interactive
```

Стартиране след инсталация (3 терминала):
```bash
# Терминал 1 — Lavalink
start_lavalink.bat

# Терминал 2 — Bot
start_bot.bat

# Терминал 3 — Dashboard (опционално)
start_dashboard.bat
```

Отвори dashboard: http://localhost:8080

---

## 🛠️ Ръчен старт (класическият начин)

### 1. Предварителни изисквания
- **Python 3.11+**
- **Lavalink v4 сървър** (трябва да работи отделно — виж долу)
- **FFmpeg** (за аудио декодиране)

### 2. Инсталация

```bash
# Клонирай репото
cd E:\DrusaBoT

# Създай виртуална среда
python -m venv .venv
.venv\Scripts\activate

# Инсталирай зависимости
pip install -r requirements.txt
```

### 3. Конфигурация (`.env`)

Копирай `.env.example` → `.env` и попълни:

```bash
copy .env.example .env
```

**Минимално задължително:**
```env
DISCORD_TOKEN=твоят_бот_токен_от_Developer_Portal
LAVALINK_URI=localhost:2333
LAVALINK_PASSWORD=youshallnotpass
DASHBOARD_SECRET_KEY=твоя_силна_тайна_ключ_мин_32_символа
DASHBOARD_USERNAME=admin
DASHBOARD_PASSWORD=твоя_парола
```

**Опционално (за PostgreSQL):**
```env
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/DrusaBoT
```
> Ако липсва → използва се `sqlite+aiosqlite:///DrusaBoT.db` (локален файл).

### 4. Стартиране на Lavalink (отделно)

Трябва да имаш работещ Lavalink v4 сървър. Най-лесно чрез Java JAR:

```bash
# Изтегли Lavalink.jar от https://github.com/lavalink-devs/Lavalink/releases
java -jar Lavalink.jar
```
По подразбиране слуша на `localhost:2333` с парола `youshallnotpass` (съвпада с `.env`).

### 5. Стартиране на бота

```bash
.venv\Scripts\activate
python -m bot.main
```

### 6. Dashboard (опционално)

```bash
# В нов терминал
.venv\Scripts\activate
python -m bot.dashboard.dashboard
```
Отвори: http://localhost:8080

---

## 📦 Основни зависимости (`requirements.txt`)

| Пакет | Назначение |
|--------|------------|
| `discord.py>=2.4.0` | Discord API wrapper |
| `wavelink>=3.0.0` | Lavalink клиент (v4 protocol) |
| `sqlalchemy>=2.0` | ORM за SQLite/PostgreSQL |
| `aiosqlite` | Async SQLite драйвер |
| `asyncpg` | Async PostgreSQL драйвер |
| `fastapi` | Web dashboard API |
| `uvicorn` | ASGI сървър за dashboard |
| `pydantic` | Валидация на настройки |
| `python-jose[cryptography]` | JWT auth за dashboard |
| `passlib[bcrypt]` | Password hashing |
| `python-dotenv` | .env конфигурация |
| `openai>=1.30.0` | AI chat клиент (OpenAI-compatible / OpenRouter) |
| `yarl`, `aiohttp` | HTTP клиент за Lavalink/YouTube |

---

## 🎮 Discord команди (Slash Commands)

| Категория | Команди |
|-----------|---------|
| **Playback** | `/play`, `/pause`, `/resume`, `/stop`, `/skip`, `/seek` |
| **Queue** | `/queue`, `/clear`, `/shuffle`, `/loop` (off/track/queue), `/remove`, `/move` |
| **Playlist** | `/playlist save`, `/playlist load`, `/playlist list`, `/playlist delete` |
| **Settings** | `/settings volume`, `/settings source`, `/settings autoplay`, `/settings djrole` |
| **Admin** | `/restart`, `/reload`, `/sync`, `/debug` |
| **AI Chat** | `!chat`, `!clear-chat`, `!chat-config` (hybrid: prefix + slash) |

> Всички команди са **slash commands** — синхронизират се автоматично при старт (`/sync` за принудително).

---

## 🌐 Dashboard API (FastAPI)

| Endpoint | Метод | Описание | Auth |
|----------|-------|----------|------|
| `/api/guilds` | GET | Списък с гилдии на бота | ✅ JWT |
| `/api/guilds/{id}` | GET | Детайли за гилдя | ✅ JWT |
| `/api/settings` | GET/PATCH | Гледане/промяна на настройки | ✅ JWT |
| `/api/health/lavalink` | GET | Health check на Lavalink нод | ✅ JWT |
| `/api/chat` | POST | AI chat completion | ✅ Bearer |
| `/api/chat/config` | GET | AI конфигурация | ❌ |
| `/api/chat/history/{guild_id}/{user_id}` | GET | История на разговори | ❌ |
| `/api/chat/history/{guild_id}/{user_id}` | DELETE | Изчистване на история | ✅ Bearer |
| `/auth/login` | POST | JWT login (username/password) | ❌ |
| `/auth/logout` | POST | Изход | ✅ JWT |

**CORS**: Конфигурира се чрез `DASHBOARD_CORS_ORIGINS` (по подразбиране `http://localhost:8080`).

---

## 🗄️ База данни (SQLAlchemy 2.0)

### Модели (`bot/database/models.py`)

| Модел | Описание |
|-------|----------|
| `Guild` | Гилдия — настройки, DJ role, prefix |
| `User` | Потребител — плейлисти, история |
| `Playlist` | Запазени плейлисти (name, tracks JSON) |
| `GuildSettings` | Гласност, източник, autoplay, DJ role |

### Репозитори (`bot/database/repository.py`)
- `GuildRepository` — CRUD за гилдии
- `UserRepository` — потребители и плейлисти
- `SettingsRepository` — настройки на гилдия

---

## 🎵 Музикален плейър — ключови компоненти

### `QueueManager` (`bot/music/queue_manager.py`)
- **Пази `wavelink.Playable` обекти** — не dictionary-та → **няма лишни HTTP заявки към Lavalink при смяна на песен**
- **Лимит 500 песни** — `add()`, `add_front()`, `add_many()` хвърлят `QueueFull` ако е пълен
- **Loop modes**: `OFF`, `TRACK`, `QUEUE`
- **History** — за `/back` функционалност

### `Player` (`bot/music/player.py`)
- Управлява `wavelink.Player` инстанс за всяка гилдя
- **Autoplay** с multi-tier fallback:
  1. YouTube Music playlist (related)
  2. YouTube Music search (same artist)
  3. Artist search
  4. YouTube search
- **Random pick от топ 10** за разнообразие
- **Circuit breaker** — след 3 неуспеха спре autoplay за 5 мин

### `LavalinkClient` (`bot/music/lavalink/client.py`)
- **Health check** — `GET /v4/info` на Lavalink
- **Exponential backoff reconnect** — 2s base, max 5min, jitter, макс 10 опита
- **Graceful shutdown** — спира reconnect task при `close()`

---

## 🤖 AI Chat асистент (OpenRouter / OpenAI-compatible)

DrusaBoT има вграден AI асистент, който работи с всеки OpenAI-compatible API — **OpenRouter** (безплатни модели), **OpenAI**, или локален сървър.

### Конфигурация (`.env`)

```env
# Включи AI
AI_ENABLED=true

# Provider (omniroute = OpenAI-compatible endpoint)
AI_PROVIDER=omniroute

# OpenRouter (безплатни модели)
OMNIROUTE_BASE_URL=https://openrouter.ai/api/v1
OMNIROUTE_API_KEY=sk-or-v1-твоят_ключ
# Fallback ключове (при rate limit / insufficient credits)
OMNIROUTE_API_KEYS_FALLBACK=sk-or-v1-втори_ключ,sk-or-v1-трети_ключ

# Модел (безплатни OpenRouter модели)
AI_DEFAULT_MODEL=openai/gpt-oss-20b:free
# Други free опции:
#   meta-llama/llama-3.3-70b-instruct:free
#   qwen/qwen3-next-80b-a3b-instruct:free

AI_SYSTEM_PROMPT=You are a helpful Discord music bot assistant...
AI_MAX_HISTORY=10
AI_TEMPERATURE=0.7
```

### Discord команди

| Команда | Описание |
|---------|----------|
| `!chat <въпрос>` или `/chat` | Задай въпрос на AI асистента |
| `!clear-chat` или `/clear-chat` | Изчисти историята на разговора |
| `!chat-config` или `/chat-config` | Покажи текущата AI конфигурация |

> Командите са **hybrid** — работят както с prefix (`!`), така и като slash commands (`/`).

### Dashboard API

| Endpoint | Метод | Описание | Auth |
|----------|-------|----------|------|
| `/api/chat` | POST | Изпрати съобщение към AI | ✅ Bearer |
| `/api/chat/config` | GET | AI конфигурация | ❌ |
| `/api/chat/history/{guild_id}/{user_id}` | GET | История на разговори | ❌ |
| `/api/chat/history/{guild_id}/{user_id}` | DELETE | Изчисти история | ✅ Bearer |

### Автоматичен fallback

AI сервисът автоматично превключва на резервен ключ при:
- **429** (rate limit)
- **402** (insufficient credits)

Логва: `Rotated to fallback API key #2`

---

## 🔐 Dashboard Auth & Security

- **JWT (HS256)** — access token 15мин, refresh 7 дни
- **Забранен default secret** — ако `DASHBOARD_SECRET_KEY=changeme` → 500 Internal Server Error
- **Pydantic валидация** на `/api/settings`:
  - `volume`: 0–100
  - `source`: regex `^(youtube|youtube_music|soundcloud|bandcamp)$`
  - `autoplay`, `dj_role_id`: boolean coercion

---

## 🧪 Тестване

```bash
.venv\Scripts\activate
pytest -v
```

**Тестове (12 общи):**
- `test_database.py` — connection pool, таблици
- `test_queue_manager.py` — queue ops, loop modes, history limit
- `test_search_helpers.py` — URL detection, source normalization, fallback uniqueness
- `test_dashboard_routes.py` — auth, validation (422 на грешни данни)

---

## 🛠️ Полезни команди

```bash
# Линтинг (ако имаш ruff/flake8)
ruff check bot/

# Типове (ако имаш pyright/mypy)
pyright bot/

# Форматиране
black bot/

# Изпълнение на един тест
pytest tests/test_queue_manager.py::QueueManagerTests::test_loop_queue_rotates_tracks -v
```

---

## 📝 .env.example (пълен)

```env
# === DISCORD ===
DISCORD_TOKEN=your_bot_token_here
DISCORD_CLIENT_ID=123456789012345678
DISCORD_CLIENT_SECRET=your_client_secret

# === LAVALINK ===
LAVALINK_URI=localhost:2333
LAVALINK_PASSWORD=youshallnotpass
LAVALINK_SECURE=false

# === DATABASE ===
# SQLite (default, local file)
DATABASE_URL=sqlite+aiosqlite:///DrusaBoT.db
# PostgreSQL (production)
# DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/DrusaBoT

# === DASHBOARD ===
DASHBOARD_HOST=0.0.0.0
DASHBOARD_PORT=8080
DASHBOARD_SECRET_KEY=your_super_secret_key_min_32_chars
DASHBOARD_USERNAME=admin
DASHBOARD_PASSWORD=your_secure_password
DASHBOARD_CORS_ORIGINS=http://localhost:8080,http://127.0.0.1:8080

# === OPTIONAL ===
LOG_LEVEL=INFO
YTMUSIC_COOKIES_FILE=ytmusic_cookies.json  # за YouTube Music качество
```

---

## 🎯 Добра практика за разработка

1. **Никога не commit-ваш `.env`** — е в `.gitignore`
2. **Тествай преди push** — `pytest -v` трябва да минава
3. **Type hints** — ползвай type hints везде (pyright strict)
4. **Embeds** — използвай `bot.utils.embeds` за консистентен стил
5. **Permissions** — проверявай чрез `bot.utils.permissions` (DJ role, voice channel, admin)

---

## 📄 Лиценз

MIT License — свободно за използване, модификация и дистрибуция.

---

## 🤝 Принос

1. Forkни репото
2. Създай feature branch (`git checkout -b feature/amazing-feature`)
3. Commitни промените (`git commit -m 'Add amazing feature'`)
4. Pushни (`git push origin feature/amazing-feature`)
5. Отвори Pull Request

---

**Направил с ❤️ за Discord общността** — приятно слушане! 🎧