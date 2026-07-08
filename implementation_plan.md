# Implementation Plan

**Overview:**
Convert the existing Discord music bot from slash commands to prefix-based commands, add server/channel restrictions, implement a comprehensive access control system (whitelist, blacklist, self-registration, audit logging), add 24/7 mode with auto-recovery, and centralize all IDs in the config module.

This plan extends the previous plan with 14 additional requirements covering user mention support, access requests, blacklist, audit logging, 24/7 mode, Lavalink auto-recovery, expanded status/whoami commands, and channel enforcement exceptions. The existing Lavalink, queue management, embed system, and database infrastructure remain mostly untouched; only new tables and fields are added.

[Types]
**New config fields** in `bot/config.py` (some already defined in previous plan):
- `guild_id: int = 1074037877899542538`
- `music_channel_id: int = 1097945134630445227`
- `owner_id: int = 954887574248374322`

**New database tables:**
1. `approved_users` — user_id TEXT PK, username TEXT, display_name TEXT, added_by TEXT, added_at TIMESTAMP
2. `access_requests` — id INTEGER PK AUTOINCREMENT, user_id TEXT, username TEXT, display_name TEXT, guild TEXT, requested_at TIMESTAMP, status TEXT DEFAULT 'pending' (pending/approved/denied)
3. `blacklisted_users` — user_id TEXT PK, username TEXT, display_name TEXT, added_by TEXT, added_at TIMESTAMP
4. `audit_logs` — id INTEGER PK AUTOINCREMENT, action TEXT, target_user_id TEXT, target_username TEXT, moderator_id TEXT, timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
5. `bot_settings` — key TEXT PK, value TEXT — for 24/7 mode state persistence (`247_enabled` = true/false)

**New cog classes:**
- `AdminCommands` (in `bot/cogs/admin_commands.py`) — owner commands, access requests, blacklist, whitelist, maintenance

[Files]
**Modified files (6):**
1. `bot/config.py` — Add `guild_id`, `music_channel_id`, `owner_id` fields
2. `bot/core/bot.py` — Enable `message_content` intent, prefix `!`, remove slash sync, add `on_ready` uptime tracking, add Lavalink auto-reconnect with exponential backoff, update `on_message`, update `setup_hook` cogs list, add 24/7 auto-join logic in `on_ready`
3. `bot/cogs/music_commands.py` — Rewrite all 14 commands: convert from `@app_commands.command` to `@commands.command`, add guild/channel checks, add authorization checks (owner > blacklist > whitelist > deny), allow `!help`, `!ping`, `!whoami`, `!requestaccess` outside music channel, convert parameter types from interaction to ctx
4. `bot/core/errors.py` — Remove `on_application_command_error` handler, remove `app_commands` import
5. `.env.example` — Add `GUILD_ID`, `MUSIC_CHANNEL_ID`, `OWNER_ID` variables
6. `README.md` — Full documentation: prefix commands, whitelist, blacklist, access requests, 24/7 mode, recovery, channel restrictions

**New files (1):**
7. `bot/cogs/admin_commands.py` — Complete admin/access control cog with all management commands

[Functions]
**New functions in `bot/cogs/admin_commands.py`:**

1. `AdminCommands.__init__(self, bot)` — Initialize cog, store bot reference
2. `AdminCommands._is_owner(self, ctx)` — Check `ctx.author.id == config.owner_id`
3. `AdminCommands._resolve_user(ctx, user_input: str)` — Static method: parse raw ID string or mention (`<@123>`, `<@!123>`) to return resolved user ID string. Handles both `123456789` and `@User` mention formats.
4. `AdminCommands._log_audit(self, action, target_user_id, target_username, moderator_id)` — Insert audit log entry
5. `AdminCommands.adduser(self, ctx, *, user_input: str)` — `!adduser <id_or_mention>` — Owner-only. Resolves mention/ID. Inserts into approved_users. Audit log. Response: "✅ User added successfully."
6. `AdminCommands.removeuser(self, ctx, *, user_input: str)` — `!removeuser <id_or_mention>` — Owner-only. Resolves mention/ID. Deletes from approved_users. Audit log. Response: "✅ User removed successfully."
7. `AdminCommands.listusers(self, ctx)` — `!listusers` — Owner-only. Query approved_users with username, display_name, user_id. Display embed.
8. `AdminCommands.requestaccess(self, ctx)` — `!requestaccess` — Anyone. Insert into access_requests. Notify owner via DM if possible. Response: "✅ Your access request has been submitted."
9. `AdminCommands.pendingrequests(self, ctx)` — `!pendingrequests` — Owner-only. Show pending access_requests as embed.
10. `AdminCommands.approve(self, ctx, *, user_input: str)` — `!approve <id_or_mention>` — Owner-only. Set status='approved'. Add to approved_users. Audit log.
11. `AdminCommands.deny(self, ctx, *, user_input: str)` — `!deny <id_or_mention>` — Owner-only. Set status='denied'. Audit log.
12. `AdminCommands.blacklist(self, ctx, *, user_input: str)` — `!blacklist <id_or_mention>` — Owner-only. Insert into blacklisted_users. Audit log.
13. `AdminCommands.unblacklist(self, ctx, *, user_input: str)` — `!unblacklist <id_or_mention>` — Owner-only. Delete from blacklisted_users. Audit log.
14. `AdminCommands.whoami(self, ctx)` — `!whoami` — Anyone. Display embed with username, display_name, user ID, guild, channel, access status, blacklist status.
15. `AdminCommands.status(self, ctx)` — `!status` — Anyone. Display embed: guild ID, music channel ID, Lavalink status, queue length, current track, bot uptime.
16. `AdminCommands.toggle_247(self, ctx, *, state: str)` — `!247 on` or `!247 off` — Owner-only. Save to bot_settings table. Response: "✅ 24/7 mode enabled/disabled."
17. `AdminCommands._get_uptime(self)` — Helper: return formatted uptime string from bot start time
18. `AdminCommands._get_blacklist_status(self, user_id)` — Query blacklisted_users table, return bool

**New functions in `bot/core/bot.py`:**
19. `Bot._start_time` — Attribute: `datetime.utcnow()` set in `on_ready`
20. `Bot._lavalink_reconnect_attempt` — Attribute: int counter for exponential backoff
21. Bot.on_ready — Add: store start time, if 24/7 enabled auto-join the music channel voice
22. Bot._auto_reconnect_lavalink(self) — Background task: retry with exponential backoff (1s, 2s, 4s, 8s, 16s, max 60s), log failures
23. Bot.on_wavelink_node_disconnected — Trigger `_auto_reconnect_lavalink()`

**Modified functions in `bot/cogs/music_commands.py`:**
24. `MusicCommands._check_guild_and_channel(self, ctx)` — Modified: allow `!help`, `!ping`, `!whoami`, `!requestaccess` outside music channel; reject all other music commands
25. `MusicCommands._require_authorized(self, ctx)` — Modified: check order: owner (pass) > blacklisted (deny with "❌ You are blacklisted.") > approved (pass) > deny (send "❌ You are not authorized to use this bot.")
26. All 14 music commands — Modified: add `if not await self._check_guild_and_channel(ctx): return` and `if not await self._require_authorized(ctx): return` at start

**Modified functions in `bot/database/database.py`:**
27. `_create_tables(conn)` — Add 5 new tables: approved_users, access_requests, blacklisted_users, audit_logs, bot_settings

**Modified functions in `bot/core/errors.py`:**
28. Remove `on_application_command_error` method
29. Remove `from discord import app_commands` import

[Classes]
**New class:**
1. `AdminCommands(commands.Cog)` — `bot/cogs/admin_commands.py` — 17 methods covering adduser, removeuser, listusers, requestaccess, pendingrequests, approve, deny, blacklist, unblacklist, whoami, status, 247 toggle, helpers. Has `setup(bot)` async function.

**Modified classes:**
2. `Bot(commands.Bot)` — `bot/core/bot.py` — New attributes: `_start_time`, `_lavalink_reconnect_attempt`. Modified: `__init__` (intents, prefix), `setup_hook` (cogs list), `on_ready` (uptime, 24/7 join, remove slash sync), `on_message` (process_commands). New: auto-reconnect logic.
3. `MusicCommands(commands.Cog)` — `bot/cogs/music_commands.py` — All 14 commands converted to prefix, added guild/channel/authorization checks, channel exceptions for non-music commands.
4. `ErrorHandler(commands.Cog)` — `bot/core/errors.py` — Removed `on_application_command_error`, cleaned imports.

**Removed classes:** None.

[Dependencies]
**No new dependencies.** All functionality uses `discord.py` built-in prefix command support and `sqlite3` (stdlib). No packages to install.

[Testing]
**Manual verification checklist after implementation.** No test framework exists; verify by inspecting all modified files.

Verification items:
- [ ] Config.guild_id == 1074037877899542538
- [ ] Config.music_channel_id == 1097945134630445227
- [ ] Config.owner_id == 954887574248374322
- [ ] .env.example has GUILD_ID, MUSIC_CHANNEL_ID, OWNER_ID
- [ ] message_content intent enabled in bot.py
- [ ] command_prefix = "!" in bot.py
- [ ] No @app_commands.command decorators in music_commands.py
- [ ] No app_commands imports in music_commands.py
- [ ] No self.tree.sync() in bot.py
- [ ] Guild check: commands silently ignored outside GUILD_ID
- [ ] Channel check: music commands blocked outside MUSIC_CHANNEL_ID with error message
- [ ] Channel exceptions: !help, !ping, !whoami, !requestaccess work outside music channel
- [ ] Authorization order: owner passes, blacklisted blocked, whitelisted passes, others blocked
- [ ] !adduser accepts both @mention and raw ID
- [ ] !removeuser accepts both @mention and raw ID
- [ ] !listusers shows username, display_name, user_id
- [ ] !requestaccess creates pending entry and notifies owner
- [ ] !pendingrequests shows pending requests
- [ ] !approve accepts @mention or ID, adds to approved_users
- [ ] !deny accepts @mention or ID, marks as denied
- [ ] !blacklist prevents all command access
- [ ] !unblacklist removes from blacklist
- [ ] !whoami shows: username, display name, ID, guild, channel, access status, blacklist status
- [ ] !status shows: guild ID, music channel ID, Lavalink status, queue length, current track, uptime
- [ ] !247 on/off persists to bot_settings SQLite table
- [ ] audit_logs table records: adduser, removeuser, approve, deny, blacklist, unblacklist
- [ ] approved_users table has: user_id, username, display_name, added_by, added_at
- [ ] access_requests table has: id, user_id, username, display_name, guild, requested_at, status
- [ ] blacklisted_users table has: user_id, username, display_name, added_by, added_at
- [ ] bot_settings table has: key, value
- [ ] Lavalink auto-reconnect with exponential backoff on disconnect
- [ ] README.md documents all features

[Implementation Order]
**Eight sequential steps following dependency order: config → database → core → errors → admin_cog → music_cog → env → docs.**

1. Modify `bot/config.py` — Add `guild_id`, `music_channel_id`, `owner_id` fields to Config class
2. Modify `bot/database/database.py` — Add 5 new tables: `approved_users`, `access_requests`, `blacklisted_users`, `audit_logs`, `bot_settings` in `_create_tables()`
3. Modify `bot/core/bot.py` — Enable `message_content`, set prefix `!`, remove slash sync, add uptime tracking, add Lavalink auto-reconnect with exponential backoff, add 24/7 auto-join in `on_ready`, update `on_message` to process commands, update `setup_hook` cogs list
4. Modify `bot/core/errors.py` — Remove `on_application_command_error` and `app_commands` import
5. Create `bot/cogs/admin_commands.py` — Complete new cog: adduser, removeuser, listusers, requestaccess, pendingrequests, approve, deny, blacklist, unblacklist, whoami, status, 247 toggle, audit logging, mention resolution
6. Rewrite `bot/cogs/music_commands.py` — Convert 14 commands from slash to prefix, add guild/channel/auth checks, channel exceptions for non-music commands
7. Update `.env.example` — Add GUILD_ID, MUSIC_CHANNEL_ID, OWNER_ID
8. Update `README.md` — Full documentation of all features