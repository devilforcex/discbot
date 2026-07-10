"""
Interactive Help Menu — inspired by Cortex help menu screenshot.
- Overview embed with Total Categories / Total Commands / Made with ❤️ by Steel
- Category dropdown (Select a category)
- Per-category embeds
- Link buttons: Support Server, Invite Bot, Vote/Website
"""

from __future__ import annotations

import logging
from typing import Dict, List

import discord

from bot.music.emoji import EMOJI

logger = logging.getLogger(__name__)

# Category definitions — mirrors bot commands
CATEGORIES: Dict[str, Dict] = {
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


def _total_commands() -> int:
    return sum(len(cat["commands"]) for cat in CATEGORIES.values())


def _total_categories() -> int:
    return len(CATEGORIES)


def build_main_help_embed(bot_user: discord.ClientUser | None = None) -> discord.Embed:
    """Main overview like Cortex Help Menu screenshot."""
    total_cats = _total_categories()
    total_cmds = _total_commands()

    embed = discord.Embed(
        title="DrusaBota Help Menu",
        description=(
            f"Select a category from the dropdown menu below\n"
            f"**Total Categories:** {total_cats}\n"
            f"**Total Commands:** {total_cmds}\n"
        ),
        color=0x8B5CF6,  # violet
    )

    # Thumbnail — bot avatar if available else Steel brand placeholder
    if bot_user and bot_user.display_avatar:
        embed.set_thumbnail(url=bot_user.display_avatar.url)
    else:
        # Fallback: use a generic music icon
        embed.set_thumbnail(url="https://cdn.discordapp.com/embed/avatars/0.png")

    # Categories list similar to second screenshot (Main, Filters, etc)
    # Build two columns like Cortex: left column main categories
    # We'll show as fields for readability
    cat_list_text = ""
    for key, cat in CATEGORIES.items():
        cat_list_text += f"{cat['emoji']} **{cat['label']}** — {cat['description']}\n"

    embed.add_field(name="Categories", value=cat_list_text[:1024], inline=False)

    embed.set_footer(text="Made with ❤️ by Steel • DrusaBota is made by Steel")
    # Add footer icon if bot user
    # embed.set_footer(text=..., icon_url=bot_user.display_avatar.url) if needed

    return embed


def build_category_embed(category_key: str, bot_user: discord.ClientUser | None = None) -> discord.Embed:
    cat = CATEGORIES.get(category_key)
    if not cat:
        return build_main_help_embed(bot_user)

    embed = discord.Embed(
        title=f"{cat['emoji']} {cat['label']} Commands",
        description=f"{cat['description']}\n**Total Commands in category:** {len(cat['commands'])}",
        color=0x8B5CF6,
    )

    if bot_user and bot_user.display_avatar:
        embed.set_thumbnail(url=bot_user.display_avatar.url)

    # Build commands list
    for cmd, desc in cat["commands"]:
        embed.add_field(name=cmd, value=desc, inline=False)

    embed.set_footer(text=f"DrusaBota | {cat['label']} • Made with ❤️ by Steel • Use dropdown to switch category")
    return embed


class HelpCategorySelect(discord.ui.Select):
    def __init__(self, bot=None):
        self.bot = bot
        options = []
        for key, cat in CATEGORIES.items():
            options.append(
                discord.SelectOption(
                    label=cat["label"],
                    value=key,
                    emoji=cat["emoji"],
                    description=cat["description"][:100],
                )
            )
        # Add extra option to go back to main menu
        options.insert(
            0,
            discord.SelectOption(
                label="Home",
                value="__home__",
                emoji="🏠",
                description="Back to main help overview",
            ),
        )

        super().__init__(
            placeholder="Select a category",
            min_values=1,
            max_values=1,
            options=options[:25],
            row=0,
        )

    async def callback(self, interaction: discord.Interaction):
        value = self.values[0]
        bot_user = interaction.client.user if hasattr(interaction.client, "user") else None

        if value == "__home__":
            embed = build_main_help_embed(bot_user)
        else:
            embed = build_category_embed(value, bot_user)

        await interaction.response.edit_message(embed=embed, view=self.view)


class HelpView(discord.ui.View):
    """Interactive help view with category dropdown + link buttons matching screenshot."""

    def __init__(self, bot=None, support_url: str | None = None, invite_url: str | None = None, vote_url: str | None = None):
        super().__init__(timeout=180)
        self.bot = bot

        # Category select
        self.add_item(HelpCategorySelect(bot=bot))

        # Link buttons like Support Server / Invite Bot / Vote in screenshot
        # If URLs not provided, use placeholders or env config
        # Support Server
        if support_url:
            self.add_item(
                discord.ui.Button(
                    label="Support Server",
                    style=discord.ButtonStyle.link,
                    url=support_url,
                    emoji="💚",
                    row=1,
                )
            )
        else:
            # Fallback placeholder button (disabled if no URL)
            # We'll still add with github as default
            self.add_item(
                discord.ui.Button(
                    label="Support Server",
                    style=discord.ButtonStyle.link,
                    url="https://discord.gg/",
                    emoji="💚",
                    row=1,
                )
            )

        if invite_url:
            self.add_item(
                discord.ui.Button(
                    label="Invite Bot",
                    style=discord.ButtonStyle.link,
                    url=invite_url,
                    emoji="🤖",
                    row=1,
                )
            )
        else:
            self.add_item(
                discord.ui.Button(
                    label="Invite Bot",
                    style=discord.ButtonStyle.link,
                    url="https://discord.com/oauth2/authorize?client_id=YOUR_CLIENT_ID&scope=bot",
                    emoji="🤖",
                    row=1,
                )
            )

        # Third button: Vote or Website / GitHub
        if vote_url:
            self.add_item(
                discord.ui.Button(
                    label="Website",
                    style=discord.ButtonStyle.link,
                    url=vote_url,
                    emoji="🌐",
                    row=1,
                )
            )
        else:
            self.add_item(
                discord.ui.Button(
                    label="GitHub",
                    style=discord.ButtonStyle.link,
                    url="https://github.com/devilforcex/discbot",
                    emoji="💻",
                    row=1,
                )
            )

    async def on_timeout(self):
        for child in self.children:
            if isinstance(child, discord.ui.Select):
                child.disabled = True
        # Buttons with link style cannot be disabled, so keep them
