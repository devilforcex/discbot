# Design System — Nightmare Bots / Steel

**Source:** `docs/reference-nightmare-bots.html` (user-provided landing)  
**Applies to:** public landing (Pages/Netlify) + live FastAPI music dashboard + Discord embed color accents

---

## Brand

| Token | Value | Use |
|-------|-------|-----|
| Brand mark | `NB` / gradient square | Logo badge |
| Product name (landing) | Nightmare Bots / Steel | Marketing site |
| Product name (bot) | Nightmare Music / DiscBot | In-app dashboard |
| Accent A | Violet `#8B5CF6` (violet-500) | Primary accent, links, badges |
| Accent B | Fuchsia `#E879F9` (fuchsia-400) | Gradients, secondary |
| Gradient CTA | `from-violet-600 to-fuchsia-600` | Primary filled buttons |
| Gradient text | `from-violet-400 via-fuchsia-400 to-white` | Hero headline |

---

## Color palette

```
Background base:     #050505
Background elevated: #09090b / zinc-950
Surface / card:      rgba(255,255,255,0.03)  + blur(10px)  → .glass
Surface hover:       rgba(255,255,255,0.06) + violet border glow
Border subtle:       rgba(255,255,255,0.05)  → border-white/5
Border strong:       rgba(255,255,255,0.10)  → border-white/10
Text primary:        #ffffff
Text body:           #d4d4d8  (zinc-300)
Text muted:          #a1a1aa  (zinc-400)
Text faint:          #71717a  (zinc-500)
Text mono cmd:       violet-400 / fuchsia-400 / blue-400 by category
Success:             #2ecc71 (optional for live status)
Danger:              #e74c3c
Selection:           rgba(139, 92, 246, 0.3)
```

### Ambient glows
- Top-left: `bg-violet-900/20` blur 128px
- Bottom-right: `bg-fuchsia-900/10` blur 128px

---

## Typography

| Role | Spec |
|------|------|
| Font | **Inter** 300 / 400 / 500 / 600 |
| Hero | 5xl → 8xl, font-medium, tracking-tight |
| Section title | 3xl → 4xl, font-medium |
| Body | text-sm / text-base, zinc-400, font-light on marketing |
| Command chip | font-mono, text-xs, colored bg-tint |
| Labels | text-xs, zinc-400, font-medium |

---

## Components (landing)

### Glass card
```css
.glass {
  background: rgba(255, 255, 255, 0.03);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.05);
}
.glass-hover:hover {
  background: rgba(255, 255, 255, 0.06);
  border-color: rgba(139, 92, 246, 0.3);
  box-shadow: 0 0 30px -5px rgba(139, 92, 246, 0.15);
}
```
Radius: `rounded-2xl` (cards), `rounded-lg` (inputs/buttons)

### Buttons
| Variant | Classes |
|---------|---------|
| Primary solid | `bg-white text-black rounded-lg text-sm font-semibold hover:bg-zinc-200` |
| Ghost | `border border-zinc-800 bg-zinc-900/50 text-zinc-300 hover:text-white` |
| Gradient | `bg-gradient-to-r from-violet-600 to-fuchsia-600 text-white shadow-violet-500/20` |
| Subtle card CTA | `bg-white/5 hover:bg-white/10 border border-white/5` |

### Live pill
```
border-violet-500/30 bg-violet-500/10 text-violet-300
+ pinging green/violet dot
```

### Command row
- Mono chip: `!play` in `bg-violet-500/10 text-violet-400`
- Category tint: Music=violet, Admin=fuchsia, Utility=blue
- Filter chips: active = violet tint; idle = zinc-800/50

### Icons
- Library: **Iconify** `solar:*` set (linear style)
- Examples: `solar:music-note-slider-linear`, `solar:bolt-circle-linear`

### Scrollbar
- Track `#09090b`, thumb `#27272a`, hover `#3f3f46`, width 8px

---

## Dashboard layout (live app — same tokens)

Hero mock in landing shows sidebar + main grid. Live dashboard should mirror:

```
┌─ Sidebar (w-64, border-r white/5) ─┐  ┌─ Main ────────────────────┐
│ [NB] Nightmare Music               │  │ Header: status + latency  │
│ • Overview                         │  │                           │
│ • Player  ← active violet tint     │  │ Glass: Now Playing card   │
│ • Queue                            │  │  art | title | progress    │
│ • Settings                         │  │  [⏯][⏭][⏹][🔀] vol     │
│ • Lavalink                         │  │                           │
│                                    │  │ Glass: Queue list         │
│ ● Online  ·  Lavalink 12ms         │  │ Glass: Stats grid 3-col   │
└────────────────────────────────────┘  └───────────────────────────┘
```

### Dashboard-specific components
- **Now Playing art**: rounded-xl, violet border glow when playing
- **Progress bar**: track zinc-800, fill gradient violet→fuchsia
- **Control buttons**: circular/square glass, hover violet border
- **Stat tiles**: glass, icon in violet/fuchsia/blue tint circle
- **Queue rows**: hover `bg-white/5`, mono duration right-aligned

---

## Discord embed mapping (approximate)

Discord embeds can't do glass CSS, but colors align:

| State | Embed color |
|-------|-------------|
| Playing | `0x8B5CF6` (violet-500) |
| Paused | `0xF59E0B` (amber) |
| Stopped / idle | `0x27272A` (zinc-800) |
| Error | `0xEF4444` |
| Success / added | `0x22C55E` |
| Favorite | `0xEAB308` |

Buttons use Discord native styles + unicode emoji matching design language.

---

## Stack for implementation

| Surface | Stack |
|---------|-------|
| Landing / dashboard | React SPA (`web/`) + Vite + Tailwind v4 + TanStack Query |
| Discord | embeds + `discord.ui.View` buttons |

**No bot secrets on static hosts.** Landing is public marketing only.

---

## File map

| File | Role |
|------|------|
| `docs/reference-nightmare-bots.html` | Canonical design reference (this system) |
| `web/` | React SPA — landing, dashboard, player, stats, library, settings |
| `web/src/components/ui/` | UI primitives (Button, GlassCard, Toast, ErrorBoundary, etc.) |
| `web/src/features/` | Feature modules (player, stats, library, settings, landing) |
| `bot/dashboard/dashboard.py` | FastAPI app, SPA catch-all + WebSocket endpoint |
| `bot/dashboard/routes.py` | All `/api/*` routes |
| `bot/dashboard/ws_manager.py` | WebSocket connection manager |
| `docs/PROJECT_PLAN.md` | Engineering phases, Windows debug checklist, archived plan summary |
