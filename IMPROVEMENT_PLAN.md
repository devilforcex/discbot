# 🎵 DiscBot — План за подобрение

**Дата:** 2026-07-10  
**База:** текущ работещ bot (prefix `!`, Lavalink v4, SQLite, FastAPI dashboard)  
**Източници:** кодът в repo, [Discord Bots Overview](https://docs.discord.com/developers/bots/overview), [Interactions](https://docs.discord.com/developers/interactions/overview), [Message Components](https://docs.discord.com/developers/components/overview)

> **Branch бележка:** тази Arena сесия е фиксирана към `arena/019f4c0b-discbot` (от master `e2531ae`). Не се създават допълнителни разклонения; работата остава тук и може да се merge-не към master след review.

---

## 1. Текущо състояние (audit)

| Област | Статус | Проблем / gap |
|--------|--------|----------------|
| Prefix команди (`!play`, `!skip`…) | ✅ Работи | Help embed още показва **slash** (`/play`) — outdated copy |
| Access control (owner/whitelist/blacklist) | ✅ Работи | — |
| Lavalink + queue + loop + autoplay | ✅ Работи | Autoplay recommendation е крехък |
| Now Playing embed | ⚠️ Частично | Само статичен текст + progress bar; **няма бутони** |
| Interactive UI (`discord.ui.View` / Buttons) | ❌ Липсва | 0 употреби на Button/View/Interaction handlers |
| Persistent player message | ❌ Липсва | Всеки `!play`/`!np` праща ново съобщение |
| Emoji consistency | ⚠️ Частично | Има emoji в titles, но help/commands не са унифицирани |
| Web dashboard | ⚠️ Минимален | Inline HTML, без real-time player, без controls, dark theme basic |
| Components V2 | ❌ Не се ползва | Discord препоръчва layout + buttons; legacy Action Rows също са OK |
| Hosting на static UI | ❌ Няма | Dashboard е FastAPI runtime; static docs/landing може на Pages/Netlify |

**Ключов извод:** backend-ът (playback, queue, auth, DB) е готов. Следващият скок е **UX слой**: interactive embed player + красив dashboard + polish на команди/emoji.

---

## 2. Визия (целеви UX)

### 2.1 Discord Embed Player (boogie.gg style)

Едно **persistent** Now Playing съобщение в music channel:

```
┌─────────────────────────────────────────────┐
│  🎵 Now Playing                             │
│  **Track Title** — Artist                   │
│  [thumbnail / artwork]                      │
│  ▓▓▓▓▓▓▓▓░░░░░░░░  1:23 / 3:45              │
│  🔊 50%  ·  🔁 Queue  ·  🤖 Autoplay ON     │
│  Requested by @user                         │
├─────────────────────────────────────────────┤
│ [⏮] [⏯] [⏭] [⏹] [🔀] [🔁] [⭐] [📋]      │
│          (emoji buttons row 1)              │
│ [🔊−] [🔊+] [🔌] [❓]                       │
│          (controls row 2)                   │
└─────────────────────────────────────────────┘
```

- Бутоните реално викат player API (pause/resume/skip/stop/…).
- Съобщението се **edit-ва** при track change / volume / loop — не се спами канал.
- Progress bar се refresh-ва на interval (напр. 10–15s) докато свири.
- При idle: „Nothing playing — use `!play`“ + disabled controls (или само ❓).

### 2.2 Web Dashboard + Landing (Nightmare Bots design system)

**Design source locked:** user HTML → `docs/reference-nightmare-bots.html`  
**Tokens:** `docs/DESIGN_SYSTEM.md`  
**Stack:** Inter + Tailwind CDN + Iconify (`solar:*`) + glassmorphism

| Token | Value |
|-------|-------|
| bg | `#050505` |
| glass | `rgba(255,255,255,0.03)` + blur 10px |
| accent | violet `#8B5CF6` → fuchsia gradient |
| text | zinc-300 / white headings |
| hover glow | violet border + soft shadow |

**Surfaces:**
1. **Static landing** `docs/index.html` — marketing, command browser → GitHub Pages / Netlify
2. **Live dashboard** `bot/dashboard/templates/index.html` + static CSS/JS — Now Playing, queue, controls
3. **Discord embeds** — color map violet/amber/zinc (see DESIGN_SYSTEM)

Live dashboard features:
- Live **Now Playing** card (title, art, progress, volume)
- Queue list
- Bot / Lavalink health tiles
- Remote controls (POST) + Bearer `DASHBOARD_SECRET_KEY`
- Poll every ~2.5s

---

## 3. Архитектура на промените

```
bot/
├── music/
│   ├── player_view.py          # NEW: discord.ui.View + buttons
│   ├── player_controller.py    # NEW: shared actions (skip/pause/…)
│   ├── embed_manager.py        # EXTEND: player embed + status line
│   ├── player_message.py       # NEW: track + edit persistent NP message
│   └── …
├── cogs/
│   ├── music_commands.py       # REFACTOR: call controller; update NP msg
│   └── …
├── dashboard/
│   ├── dashboard.py            # REFACTOR: API + serve SPA
│   ├── static/                 # NEW: CSS/JS assets
│   │   ├── css/dashboard.css
│   │   └── js/dashboard.js
│   └── templates/
│       └── index.html          # NEW: full dashboard UI
└── docs/                       # OPTIONAL: Retype static docs → Pages
```

**Принцип:** всички playback actions минават през `PlayerController`, за да:
1. `!skip` и бутон ⏭ правят едно и също
2. Dashboard POST `/api/control/skip` ползва същото
3. Auth checks (guild/channel/whitelist) са централизирани

---

## 4. Фази на имплементация

### Фаза 0 — Quick polish (1–2 часа)
**Риск: нисък | Зависимости: няма**

| # | Задача | Файл |
|---|--------|------|
| 0.1 | Поправи `help_embed()` да показва `!` prefix, не `/` | `embed_manager.py` |
| 0.2 | Добави admin команди в help (owner секция) | `embed_manager.py` |
| 0.3 | Унифицирай emoji map (constants) | `bot/music/emoji.py` (new) |
| 0.4 | Aliases: `!np`→nowplaying, `!p`→play, `!q`→queue, `!vol`→volume, `!dc`→disconnect | `music_commands.py` |

**Emoji constants (предложение):**

```python
EMOJI = {
    "play": "▶️", "pause": "⏸️", "resume": "▶️", "skip": "⏭️",
    "stop": "⏹️", "prev": "⏮️", "shuffle": "🔀", "loop_none": "➡️",
    "loop_track": "🔂", "loop_queue": "🔁", "volume": "🔊",
    "mute": "🔇", "favorite": "⭐", "queue": "📋", "disconnect": "🔌",
    "autoplay": "🤖", "music": "🎵", "error": "❌", "ok": "✅",
}
```

---

### Фаза 1 — Interactive Embed Player (core) (1–2 дни)
**Риск: среден | Discord Components (legacy Action Rows — stable)**

Според [Discord Interactions](https://docs.discord.com/developers/interactions/overview) и [Components](https://docs.discord.com/developers/components/overview):
- Buttons = interactive message components
- App получава interaction → update message / defer
- Legacy Action Rows + Buttons **няма да се deprecate-ват**; Components V2 (`IS_COMPONENTS_V2`) е optional upgrade (без classic embeds)

**Препоръка за v1:** `discord.ui.View` + `discord.ui.Button` + classic Embed (най-прост path с discord.py).  
**v2 later:** Components V2 layout (Media Gallery, Sections) ако искаш boogie-level look без classic embeds.

#### 1.1 `PlayerController` (shared actions)

```python
# bot/music/player_controller.py
class PlayerController:
    async def pause(guild_id, user) -> Result
    async def resume(guild_id, user) -> Result
    async def skip(guild_id, user) -> Result
    async def stop(guild_id, user) -> Result
    async def shuffle(guild_id, user) -> Result
    async def cycle_loop(guild_id, user) -> Result
    async def volume_delta(guild_id, user, delta: int) -> Result
    async def favorite(guild_id, user) -> Result
    async def disconnect(guild_id, user) -> Result
```

- Вътре: voice checks, auth (owner > blacklist > whitelist), queue ops
- Връща structured result → embed update + ephemeral feedback

#### 1.2 `PlayerView` (buttons)

```python
class PlayerView(discord.ui.View):
    # timeout=None + persistent custom_ids за restart-safe
    # custom_id prefix: "mb:{action}:{guild_id}"
    
    # Row 0
    previous | play_pause | skip | stop | shuffle
    # Row 1  
    loop | vol_down | vol_up | favorite | queue
```

| Button | custom_id action | Поведение |
|--------|------------------|-----------|
| ⏯ | `play_pause` | toggle pause/resume |
| ⏭ | `skip` | stop current → next from queue |
| ⏹ | `stop` | stop + clear queue |
| 🔀 | `shuffle` | shuffle queue |
| 🔁 | `loop` | cycle none → track → queue |
| 🔉 / 🔊 | `vol_down` / `vol_up` | ±10 volume, persist settings |
| ⭐ | `favorite` | save current for interaction.user |
| 📋 | `queue` | ephemeral queue embed (page 1) |
| 🔌 | `disconnect` | leave VC (owner or requester?) |

**Auth на бутон click:**
1. Interaction user must pass same whitelist as commands
2. User must be in same voice channel as bot (optional soft rule: allow volume/queue view from text)
3. Ephemeral error: „❌ You are not authorized“ / „Join the voice channel first“

#### 1.3 Persistent player message

```python
# bot/music/player_message.py
class PlayerMessageManager:
    # guild_id -> message_id (in-memory + bot_settings SQLite)
    async def ensure_player_message(guild, channel) -> Message
    async def update_now_playing(guild_id) -> None
    async def set_idle(guild_id) -> None
    async def start_progress_task(guild_id) -> None  # edit every 12s
```

**Hooks (къде да се вика update):**
- `on_wavelink_track_start` → full NP update + enable buttons
- `on_wavelink_track_end` → next or idle
- `!play` / controller actions → update
- volume/loop/autoplay changes → update footer/status line

**Persistence:**
- Save `player_message_id` + `player_channel_id` in `bot_settings` (или `guild_settings`)
- On ready: re-bind `PlayerView` with `bot.add_view(PlayerView(), message_id=…)`

#### 1.4 Command integration

| Команда | Промяна |
|---------|---------|
| `!play` | След play → update persistent NP (не праща огромен embed всеки път; optional short „Added #3“) |
| `!nowplaying` | Edit/repost player message + buttons (не само static embed) |
| `!pause/resume/skip/stop/…` | Делегират към `PlayerController` + refresh view |
| `!help` | Секция „Player buttons“ + emoji legend |

#### 1.5 Progress refresh task

- `asyncio` task per guild while playing
- Edit only if position changed meaningfully (>1s)
- Stop task on idle/disconnect
- Rate-limit: Discord message edit ~5/5s per channel → interval **≥10s** safe

---

### Фаза 2 — Embed & visual polish (0.5–1 ден)

| # | Задача |
|---|--------|
| 2.1 | Цветова схема по state: playing=green, paused=orange, stopped=dark, error=red |
| 2.2 | Status line: `▶️ Playing · 🔁 Queue · 🔊 70% · 🤖 Autoplay` |
| 2.3 | Thumbnail artwork + fallback bot avatar |
| 2.4 | Queue embed: pagination buttons (◀️ ▶️) вместо `!queue 2` only |
| 2.5 | Search results: select menu (top 5 tracks) при `!play query` без exact URL |
| 2.6 | Favorites / playlist embeds с play buttons |

**Search Select Menu (UX win):**
```
!play never gonna
→ embed "Select a track" + StringSelect (5 options)
→ user picks → play
```

---

### Фаза 3 — Красив Web Dashboard (1–2 дни)

#### 3.1 API extensions

| Endpoint | Method | Цел |
|----------|--------|-----|
| `/api/status` | GET | + uptime, 24/7 flag, version |
| `/api/nowplaying/{guild_id}` | GET | already exists — add loop/autoplay/queue_len |
| `/api/queue/{guild_id}` | GET | exists |
| `/api/control/{guild_id}/{action}` | POST | skip/pause/resume/stop/shuffle/volume (auth header) |
| `/api/events` | GET (SSE) | optional live push every 2s |
| `/api/health` | GET | liveness for reverse proxy |

**Auth:** `DASHBOARD_SECRET_KEY` as `Authorization: Bearer …` for write endpoints. Read-only local bind default.

#### 3.2 Frontend (single-page)

Структура на `templates/index.html` + static assets:

```
┌─ Sidebar ──────────────────┐  ┌─ Main ────────────────────────┐
│ 🎵 DiscBot                 │  │  Now Playing Card             │
│ • Overview                 │  │  [art] Title / Artist         │
│ • Player                   │  │  ████████░░  1:23 / 3:45      │
│ • Queue                    │  │  [⏯][⏭][⏹][🔀]  vol ──●──  │
│ • Settings                 │  ├───────────────────────────────┤
│ • Lavalink                 │  │  Queue (N tracks)             │
│                            │  │  1. …  2. …  3. …             │
│ Status: ● Online           │  ├───────────────────────────────┤
│ Lavalink: ● 12ms           │  │  Stats / Uptime / Guild info  │
└────────────────────────────┘  └───────────────────────────────┘
```

**Design tokens:** виж `docs/DESIGN_SYSTEM.md` (Nightmare Bots — violet/fuchsia glass).

**JS behavior (implemented in `static/js/dashboard.js`):**
- Poll `/api/nowplaying` + `/api/status` + `/api/queue` every 2.5s
- Control buttons → POST `/api/control/{guild}/{action}`
- Volume slider debounced → `volume` action
- Token + guild ID in localStorage

#### 3.3 FastAPI wiring — **DONE (template + static + control API)**

```python
app.mount("/static", StaticFiles(...))
templates.TemplateResponse("index.html", {"request": request, "guild_id": ...})
POST /api/control/{guild_id}/{action}  # pause|resume|skip|stop|shuffle|volume
```

Inline f-string HTML **премахнат** от `dashboard.py`.

---

### Фаза 4 — Static landing (free hosting) — **assets ready**

| File | Role |
|------|------|
| `docs/index.html` | Deployable DiscBot landing (Nightmare design) |
| `docs/reference-nightmare-bots.html` | Original design reference |
| `docs/DESIGN_SYSTEM.md` | Tokens for all UIs |

| Host | Use case | Бележка |
|------|----------|---------|
| [GitHub Pages](https://retype.com/hosting/github-pages/) | `docs/` folder | Settings → Pages → `/docs` |
| [Netlify](https://retype.com/hosting/netlify/) | drag `docs/` or git | publish directory = `docs` |
| FastAPI dashboard | live bot control | **не** е static — VPS only |

**Не** хоствай live dashboard на Pages/Netlify.

---

### Фаза 5 — Quality & production (ongoing)

| # | Задача |
|---|--------|
| 5.1 | Unit tests за `PlayerController` + queue (pytest + pytest-asyncio) |
| 5.2 | Fix `ctx.defer()` misuse (prefix commands нямат native defer като slash — ползвай typing / temp msg) |
| 5.3 | Rate-limit button spam (cooldown 1s per user) |
| 5.4 | Audit log за dashboard remote controls |
| 5.5 | Docker Compose: bot + Lavalink (+ optional dashboard) |
| 5.6 | Healthcheck endpoint + systemd examples update |
| 5.7 | Components V2 experiment (optional redesign) |

---

## 5. Discord API alignment (checklist)

От [Bots Overview](https://docs.discord.com/developers/bots/overview):

- [x] Application + Bot user + Gateway (discord.py)
- [x] Intents: `message_content`, `voice_states`, `guilds`
- [ ] **Interactions:** Buttons + Select Menus (Фаза 1–2)
- [ ] Optional: re-introduce **slash commands** alongside prefix (`/play` + `!play`) — slash дава native autocomplete
- [ ] Message Components persistence (`custom_id` + `add_view` on ready)
- [ ] Permissions: `Send Messages`, `Embed Links`, `Connect`, `Speak`, `Use External Emojis` (ако custom emoji)
- [ ] Privileged intents toggle in Developer Portal remains correct

**Slash vs Prefix:**
- Текущо: само `!` — OK за private bot
- Upgrade path: dual mode — slash за public UX, prefix за power users
- Slash + buttons = най-native Discord experience

---

## 6. Приоритетен roadmap

```
Week 1
  ├── Фаза 0 polish (help, aliases, emoji)
  ├── Фаза 1.1–1.2 Controller + PlayerView
  └── Фаза 1.3–1.4 Persistent message + command wiring

Week 2
  ├── Фаза 1.5 Progress refresh
  ├── Фаза 2 Search select + queue pagination
  └── Фаза 3 Dashboard redesign (HTML/CSS/JS + control API)

Week 3 (optional)
  ├── Фаза 4 Static docs on Pages/Netlify
  ├── Фаза 5 Tests + Docker
  └── Components V2 / dual slash commands
```

---

## 7. Acceptance criteria

### Embed player
- [ ] `!play` стартира track и показва NP message **с работещи бутони**
- [ ] ⏯ pause/resume реално спира/пуска audio
- [ ] ⏭ skip → следващ track от queue
- [ ] ⏹ stop + clear queue
- [ ] 🔀 shuffle queue
- [ ] 🔁 cycle loop modes (embed status updates)
- [ ] 🔉/🔊 volume ±10, persist to SQLite
- [ ] ⭐ favorite current track for clicker
- [ ] 📋 ephemeral queue
- [ ] Unauthorized user click → ephemeral deny
- [ ] Bot restart → buttons still work (persistent view)
- [ ] Progress bar updates while playing

### Commands / emoji
- [ ] `!help` показва `!` commands + button legend
- [ ] Aliases `!np`, `!p`, `!q`, `!vol` работят
- [ ] Единен emoji vocabulary

### Dashboard / landing
- [x] Dark glass UI (Nightmare tokens)
- [x] Live now-playing + queue (poll JS)
- [x] Control buttons + Bearer auth path
- [x] Mobile responsive layout
- [x] `/static` assets + Jinja template
- [x] Static landing in `docs/` for Pages/Netlify
- [ ] Pixel QA against reference on real bot runtime

---

## 8. Рискове и mitigation

| Риск | Mitigation |
|------|------------|
| Message edit rate limits | Progress interval ≥10s; batch status updates |
| View timeout след restart | `timeout=None` + persistent `custom_id` + `add_view` on ready |
| Button spam | per-user cooldown; disable buttons while processing |
| Auth bypass via dashboard | Bearer secret; bind 127.0.0.1; reverse proxy auth |
| Components V2 breaks embeds | Stay on classic embeds+ActionRow for v1 |
| `ctx.defer` on prefix | Replace with typing indicator / temp „Searching…“ message |
| HTML reference | ✅ locked in `docs/reference-nightmare-bots.html` + DESIGN_SYSTEM |

---

## 9. Файлове — diff summary (очаквано)

| Action | Path |
|--------|------|
| CREATE | `bot/music/emoji.py` |
| CREATE | `bot/music/player_controller.py` |
| CREATE | `bot/music/player_view.py` |
| CREATE | `bot/music/player_message.py` |
| MODIFY | `bot/music/embed_manager.py` |
| MODIFY | `bot/music/lavalink_client.py` (hooks → player message) |
| MODIFY | `bot/cogs/music_commands.py` |
| MODIFY | `bot/core/bot.py` (register persistent views) |
| MODIFY | `bot/dashboard/dashboard.py` |
| CREATE | `bot/dashboard/templates/index.html` ✅ |
| CREATE | `bot/dashboard/static/css/dashboard.css` ✅ |
| CREATE | `bot/dashboard/static/js/dashboard.js` ✅ |
| MODIFY | `bot/dashboard/dashboard.py` ✅ (Jinja + static + control API) |
| CREATE | `docs/index.html` ✅ landing |
| CREATE | `docs/reference-nightmare-bots.html` ✅ |
| CREATE | `docs/DESIGN_SYSTEM.md` ✅ |
| MODIFY | `README.md` |
| TODO | embed player modules (Фаза 0–1) |

---

## 10. Какво НЕ е в scope (засега)

- Multi-guild public SaaS bot
- Spotify OAuth user login in dashboard
- Full drag-and-drop queue on web (nice-to-have later)
- Monetization / App Directory (Discord docs mention it — not needed for private bot)
- Hosting live bot on GitHub Pages (impossible for Gateway bot)

---

## 11. Статус & следваща стъпка

| Област | Статус |
|--------|--------|
| Design system + landing | ✅ готово |
| Live dashboard UI shell + control API | ✅ готово |
| Discord embed player + buttons | ✅ готово |
| Help / aliases / emoji polish | ✅ готово |
| Persistent NP message + progress refresh | ✅ готово |
| Search select menu / queue page buttons | ⏳ Фаза 2 |
| Docker / tests | ⏳ Фаза 5 |

**Как да тестваш player-а:**
1. Стартирай Lavalink + `python bot/main.py`
2. `!play <song>` в music channel → появява се NP message с бутони
3. Натисни ⏯️ / ⏭️ / 🔁 / 🔊 — ephemeral feedback + embed update
4. Restart bot → бутоните трябва да работят (restore_views)
5. `DASHBOARD_ENABLED=true` → отвори dashboard UI

---

*Работата е на branch `arena/019f4c0b-discbot` (без допълнителни branches). Merge към master след review.*
