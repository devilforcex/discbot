"""Help categories definition."""

from __future__ import annotations

CATEGORIES: dict[str, dict] = {
    "main": {
        "label": "Main",
        "emoji": "🏠",
        "description": "Core music playback controls",
        "commands": [
            ("!play <query>", "Search with Top 5 select / play URL (alias !p)"),
            ("!pause / !resume", "Pause or resume playback"),
            ("!skip / !next", "Skip current track (alias !s)"),
            ("!stop", "Stop playback and clear queue"),
            ("!disconnect / !dc", "Leave voice channel"),
            ("!nowplaying / !np", "Show persistent player with filter dropdown + buttons"),
            ("!queue / !q", "View queue with ◀️▶️ pagination buttons"),
        ],
    },
    "filters": {
        "label": "Filters",
        "emoji": "🎛️",
        "description": "Audio filters like Bassboost, Nightcore etc (reference screenshots)",
        "commands": [
            ("!filter <name>", "Apply filter: bassboost, nightcore, vaporwave, pop, 8d, lofi..."),
            ("!filters", "List filters + interactive Select A Filter To Apply."),
            ("!filter reset", "Clear filters — back to normal"),
            ("!seek <seconds>", "Seek to position in seconds"),
            ("!forward [+10] / !rewind [-10]", "Seek forward/backward 10s (buttons ⏩/⏪)"),
            ("!replay", "Replay current track from start (⏮️)"),
        ],
    },
    "queue": {
        "label": "Queue",
        "emoji": "📋",
        "description": "Queue management, loop and autoplay",
        "commands": [
            ("!queue [page]", "Paginated queue with Shuffle/Refresh/Close"),
            ("!shuffle", "Shuffle the queue"),
            ("!loop <none/track/queue>", "Set loop mode"),
            ("!autoplay [on/off/toggle]", "Toggle autoplay recommendations"),
            ("!volume <0-100> / !vol", "Set volume, persists to DB"),
        ],
    },
    "favorites": {
        "label": "Favorites",
        "emoji": "⭐",
        "description": "Save and play your favorite tracks",
        "commands": [
            ("!favorite / !fav", "Save current track to favorites"),
            ("!favorites [page]", "List + play via ⭐ dropdown + ◀️▶️ pagination"),
        ],
    },
    "playlists": {
        "label": "Playlists",
        "emoji": "📀",
        "description": "Create and manage playlists",
        "commands": [
            ("!playlist_create <name>", "Create a new playlist"),
            ("!playlists", "List your playlists with 📀 dropdown"),
            ("!playlist_show <id>", "View tracks + Play All + track select"),
            ("!playlist_add <id>", "Add current track to playlist"),
            ("!playlist_remove <id> <pos>", "Remove track from playlist"),
            ("!playlist_play <id>", "Queue all tracks from playlist"),
        ],
    },
    "utility": {
        "label": "Utility",
        "emoji": "❓",
        "description": "Info and general commands",
        "commands": [
            ("!help", "Show this interactive help menu"),
            ("!ping", "Bot + Lavalink latency"),
            ("!status", "Bot status, uptime, queue length"),
            ("!whoami", "Your ID + access status"),
            ("!requestaccess", "Request whitelist from owner (public)"),
        ],
    },
    "admin": {
        "label": "Setup",
        "emoji": "🛠️",
        "description": "Admin / owner controls (whitelist, blacklist, 24/7)",
        "commands": [
            ("!adduser / !removeuser <@user>", "Manage whitelist (owner)"),
            ("!listusers", "List approved users"),
            ("!approve / !deny", "Handle access requests"),
            ("!pendingrequests", "Show pending requests"),
            ("!blacklist / !unblacklist", "Block/unblock users"),
            ("!247 on/off", "Toggle 24/7 voice auto-join"),
        ],
    },
}


def total_commands() -> int:
    return sum(len(cat["commands"]) for cat in CATEGORIES.values())


def total_categories() -> int:
    return len(CATEGORIES)
