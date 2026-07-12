# Implementation Plan - Debug Lavalink !play url Error

## Overview

Debug and fix the Lavalink error that occurs when using the `!play <url>` command. The primary issue is in `bot/music/search.py` line 73-74 where URL searches bypass the fallback mechanism entirely, causing failures when YouTube Music cannot load the track due to age-restriction, region-locking, or other load errors.

## Types

No new type definitions required. The existing `wavelink.LavalinkLoadException` provides all necessary error information via `error`, `severity`, and `cause` attributes.

## Files

- `bot/music/search.py` — Add URL fallback handling in `search_tracks()`
- `bot/cogs/music/playback.py` — Improve error message extraction
- `tests/test_search_helpers.py` — Add async tests for URL search behavior

## Functions

### New functions:
- `search.py::_extract_lavalink_error(exc: Exception) -> tuple[str, str]` — Extract error message and cause from LavalinkLoadException

### Modified functions:
- `search.py::search_tracks()` — Add fallback loop for URLs (currently returns immediately on line 74)
- `playback.py::play()` — Use detailed error extraction for user-facing messages

## Classes

No class modifications needed.

## Dependencies

No dependency changes.

## Testing

Run the test script to verify Lavalink connectivity and error handling:
```bash
python -r requirements.txt  # Ensure wavelink is installed
java -jar Lavalink.jar      # Start Lavalink in another terminal
python test_lavalink_url.py # Run the test
```

## Implementation Order

1. Modify `search_tracks()` to catch LavalinkLoadException for URLs and try fallback sources
2. Add `_extract_lavalink_error()` helper for better error messages
3. Update `playback.py` error handling to use extracted error info
4. Add unit tests for URL fallback behavior