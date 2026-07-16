"""Help embeds."""

from __future__ import annotations

import discord

from .categories import CATEGORIES, total_categories, total_commands


def build_main_help_embed(bot_user: discord.ClientUser | None = None) -> discord.Embed:
    total_cats = total_categories()
    total_cmds = total_commands()

    embed = discord.Embed(
        title="DrusaBota Help Menu",
        description=f"Select a category from the dropdown menu below\n**Total Categories:** {total_cats}\n**Total Commands:** {total_cmds}\n",
        color=0x8B5CF6,
    )

    if bot_user and bot_user.display_avatar:
        embed.set_thumbnail(url=bot_user.display_avatar.url)
    else:
        embed.set_thumbnail(url="https://cdn.discordapp.com/embed/avatars/0.png")

    cat_list_text = ""
    for cat in CATEGORIES.values():
        cat_list_text += f"{cat['emoji']} **{cat['label']}** — {cat['description']}\n"

    embed.add_field(name="Categories", value=cat_list_text[:1024], inline=False)
    embed.set_footer(text="Made with ❤️ by Steel • DrusaBota is made by Steel")
    return embed


def build_category_embed(
    category_key: str, bot_user: discord.ClientUser | None = None
) -> discord.Embed:
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

    for cmd, desc in cat["commands"]:
        embed.add_field(name=cmd, value=desc, inline=False)

    embed.set_footer(
        text=f"DrusaBota | {cat['label']} • Made with ❤️ by Steel • Use dropdown to switch category"
    )
    return embed
