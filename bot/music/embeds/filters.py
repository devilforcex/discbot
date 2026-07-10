"""Filter embed."""
import discord

from bot.music.emoji import COLOR_PLAYING


def filter_embed(active_filter: str = "off") -> discord.Embed:
    from bot.music.audio_filters import FILTER_INFO, get_filter_choices

    embed = discord.Embed(
        title="🎛️ Audio Filters",
        description="Select a filter from the dropdown below to enhance audio.\n"
        f"**Active:** `{active_filter}`",
        color=COLOR_PLAYING,
    )

    for value, label, desc, emoji in get_filter_choices():
        active_mark = " **(active)**" if value == active_filter else ""
        embed.add_field(
            name=f"{emoji} {label}{active_mark}",
            value=f"`{value}` — {desc}",
            inline=True,
        )

    embed.set_footer(text="Filters use Lavalink — Reset to clear • Works only while playing")
    return embed
