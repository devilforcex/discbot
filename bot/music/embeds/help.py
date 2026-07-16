"""Help embed (static version)."""

import discord

from bot.music.emoji import COLOR_PLAYING, EMOJI


def help_embed() -> discord.Embed:
    embed = discord.Embed(
        title=f"{EMOJI['music']} Music Bot Commands",
        description=(
            "Prefix: `!` · Aliases: `!p` `!np` `!q` `!vol` `!dc`\n"
            "Player has persistent buttons + filter dropdown + seek (+10/-10/Replay)."
        ),
        color=COLOR_PLAYING,
    )

    embed.add_field(
        name=f"{EMOJI['play']} Playback",
        value=(
            "`!play <query>` — Search (Top 5 select) / URL\n"
            "`!pause` / `!resume` — Pause/resume\n"
            "`!skip` — Skip track\n"
            "`!stop` — Stop & clear queue\n"
            "`!disconnect` (`!dc`) — Leave voice\n"
            "`!seek <seconds>` / `!forward` / `!rewind` / `!replay`"
        ),
        inline=True,
    )

    embed.add_field(
        name=f"{EMOJI['queue']} Queue",
        value=(
            "`!queue` (`!q`) — View queue (◀️▶️ buttons)\n"
            "`!nowplaying` (`!np`) — Player + buttons\n"
            "`!shuffle` — Shuffle queue\n"
            "`!loop <none|track|queue>`\n"
            "`!autoplay [on|off|toggle]`"
        ),
        inline=True,
    )

    embed.add_field(
        name="⚙️ Settings & utility",
        value=(
            "`!volume <0-100>` (`!vol`)\n"
            "`!ping` — Latency\n"
            "`!help` — This menu\n"
            "`!status` / `!whoami`"
        ),
        inline=True,
    )

    embed.add_field(
        name="🎛️ Filters (new)",
        value=(
            "`!filter <name>` — Apply audio filter\n"
            "`!filters` — List filters + select menu\n"
            "`!filter reset` — Clear filters\n"
            "Presets: `bassboost`, `nightcore`,\n"
            "`vaporwave`, `pop`, `8d`, `lofi`,\n"
            "`karaoke`, `tremolo`\n"
            "*Also in player dropdown*"
        ),
        inline=True,
    )

    embed.add_field(
        name=f"{EMOJI['favorite']} Favorites",
        value=(
            "`!favorite` — Save current track\n"
            "`!favorites [page]` — List + play via ⭐ menu\n"
            "*(select + ◀️▶️ pagination)*"
        ),
        inline=True,
    )

    embed.add_field(
        name="📀 Playlists",
        value=(
            "`!playlists` — Your playlists (📀 menu)\n"
            "`!playlist_show <id>` — View + play via menu\n"
            "`!playlist_create <name>`\n"
            "`!playlist_add <id>` / `remove`\n"
            "`!playlist_play <id>` — Queue all"
        ),
        inline=True,
    )

    embed.add_field(
        name="🔒 Owner",
        value=(
            "`!adduser` / `!removeuser` / `!listusers`\n"
            "`!approve` / `!deny` / `!pendingrequests`\n"
            "`!blacklist` / `!unblacklist`\n"
            "`!247 on|off`"
        ),
        inline=True,
    )

    embed.add_field(
        name="🎛️ Player components",
        value=(
            "**Dropdown Row 0:** Select A Filter To Apply.\n"
            f"**Row 1:** {EMOJI['play_pause']} pause/resume · {EMOJI['skip']} skip · "
            f"{EMOJI['stop']} stop · {EMOJI['shuffle']} shuffle · "
            f"{EMOJI['loop_queue']} loop\n"
            f"**Row 2:** {EMOJI['vol_down']}/{EMOJI['vol_up']} volume · "
            f"{EMOJI['favorite']} fav · {EMOJI['queue']} queue · "
            f"{EMOJI['disconnect']} disconnect\n"
            "**Row 3:** ⏮️ replay · ⏪ -10s · ⏩ +10s"
        ),
        inline=False,
    )

    embed.set_footer(
        text="DrusaBota • Made with ❤️ by Steel • Use dropdown to switch category • Discord link in buttons below"
    )
    return embed
