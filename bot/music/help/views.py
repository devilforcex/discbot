"""Help interactive views."""
from __future__ import annotations

import discord

from .categories import CATEGORIES
from .embeds import build_category_embed, build_main_help_embed


class HelpCategorySelect(discord.ui.Select):
    def __init__(self, bot=None):
        self.bot = bot
        options = []
        for key, cat in CATEGORIES.items():
            options.append(
                discord.SelectOption(
                    label=cat["label"], value=key, emoji=cat["emoji"], description=cat["description"][:100]
                )
            )
        options.insert(
            0,
            discord.SelectOption(label="Home", value="__home__", emoji="🏠", description="Back to main help overview"),
        )

        super().__init__(placeholder="Select a category", min_values=1, max_values=1, options=options[:25], row=0)

    async def callback(self, interaction: discord.Interaction):
        value = self.values[0]
        bot_user = interaction.client.user if hasattr(interaction.client, "user") else None
        if value == "__home__":
            embed = build_main_help_embed(bot_user)
        else:
            embed = build_category_embed(value, bot_user)
        await interaction.response.edit_message(embed=embed, view=self.view)


class HelpView(discord.ui.View):
    def __init__(self, bot=None, support_url: str | None = None, invite_url: str | None = None, vote_url: str | None = None):
        super().__init__(timeout=180)
        self.bot = bot
        self.add_item(HelpCategorySelect(bot=bot))

        # Support Server button
        self.add_item(
            discord.ui.Button(
                label="Support Server",
                style=discord.ButtonStyle.link,
                url=support_url or "https://discord.gg/",
                emoji="💚",
                row=1,
            )
        )
        self.add_item(
            discord.ui.Button(
                label="Invite Bot",
                style=discord.ButtonStyle.link,
                url=invite_url or "https://discord.com/oauth2/authorize?client_id=YOUR_CLIENT_ID&scope=bot",
                emoji="🤖",
                row=1,
            )
        )
        self.add_item(
            discord.ui.Button(
                label="Website" if vote_url else "GitHub",
                style=discord.ButtonStyle.link,
                url=vote_url or "https://github.com/devilforcex/discbot",
                emoji="🌐" if vote_url else "💻",
                row=1,
            )
        )

    async def on_timeout(self):
        for child in self.children:
            if isinstance(child, discord.ui.Select):
                child.disabled = True
