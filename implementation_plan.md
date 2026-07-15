# Implementation Plan

## Overview

Fix Lavalink YouTube playback by properly configuring the youtube-v2 plugin with cookies, correcting the Lavalink application.yml, fixing start scripts to point to the lavalink/ directory, and resolving wavelink 3.5.2 API compatibility issues in the bot code.

The current setup has Lavalink.jar and its configuration in `E:\discbot\lavalink\` but start scripts look for them in `E:\discbot\`. The `lavalink/application.yml` lacks plugin configuration entirely despite having `youtube-v2-1.18.1.jar` in the plugins folder. Additionally, the bot code uses wavelink 3.5.2 which has API changes (e.g., `Playable.search` returns `Search` object, not a plain list, and YouTube cookies support needs to be enabled).

## Types

No new type definitions needed; the existing `Config` class in `bot/config.py` already has `youtube_cookies_enabled` field which just needs to be toggled to `True`.

Minor signature changes in `bot/music/search.py` to handle the wavelink 3.5.2 `Search` return type (which inherits from `list` but has `.tracks` property for playlist results).

## Files

### Modified files:
1. **lavalink/application.yml** — Complete rewrite with youtube-v2 plugin configuration, cookie file path, and proper source settings.
2. **scripts/windows/start.bat** — Update paths to point to `lavalink/` for Lavalink.jar and application.yml.
3. **lavalink/run_lavalink.bat** — Update to use plugins from `plugins/` directory.
4. **bot/music/search.py** — Fix `search_tracks` to handle `Playable.search` returning `Search` (list subclass) and fix the source fallback logic for URL queries.

### Files to be created:
5. **E:\discbot\lavalink\plugins\** (symbolic link or copy of youtube-v2-1.18.1.jar)

### No files to delete.

## Functions

### Modified Functions:
1. `search_tracks` in `bot/music/search.py`:
   - Fix URL handling: `Playable.search` now returns `Search` (list subclass) — the truthiness check still works but playlist detection needs updating.
   - Fix the fallback chain for URL sources — when source is `None`, Lavalink auto-detects, but with youtube-v2 plugin the auto-detect should work correctly.
   - The `_extract_lavalink_error` helper function signature stays the same — already handles `LavalinkLoadException` and `NodeException`.

### No functions removed.

## Classes

### Modified Classes:
1. `LavalinkClient` in `bot/music/lavalink/client.py`:
   - The `setup` method currently creates `wavelink.Node(uri=uri, password=...)` — this is compatible with wavelink 3.5.2 (Node __init__ signature verified).
   - The `Pool.connect(client=self.bot, nodes=[node])` call is compatible with wavelink 3.5.2 signature: `(*, nodes: 'Iterable[Node]', client: 'discord.Client | None' = None, cache_capacity: 'int | None' = None)`.
   - No changes needed here except version compatibility is verified.

2. `Config` in `bot/config.py`:
   - No API changes needed. Just the default for `youtube_cookies_enabled` changes from `False` to `True`.

## Dependencies

No new Python packages needed. The venv already has wavelink 3.5.2 installed which is compatible with Lavalink v4.

The youtube-v2-1.18.1.jar plugin needs to be made available to Lavalink at runtime. This plugin goes in Lavalink's plugin directory (`lavalink/plugins/` or the configured `pluginPath`).

## Testing

Run `test_lavalink_url.py` after changes to verify Lavalink connectivity and YouTube URL resolution.
Run the bot with `python -m bot.main` to verify it starts and connects to Lavalink without errors.
Verify the start.bat script exits cleanly (invoke it and check both windows appear).

## Implementation Order

1. Update `lavalink/application.yml` with youtube-v2 plugin config, cookies, and corrected settings.
2. Copy or symlink `youtube-v2-1.18.1.jar` from plugins folder to Lavalink's plugin path.
3. Update `lavalink/run_lavalink.bat` to include the plugin path.
4. Update `scripts/windows/start.bat` to point to lavalink/ directory for Lavalink.
5. Fix `bot/music/search.py` for wavelink 3.5.2 Search return type compatibility.
6. Update `bot/config.py` default for `youtube_cookies_enabled` to True.
7. Update root `start.bat` launcher to be consistent.
8. Test the setup.