"""AI Chat Commands - !chat, !clear-chat, !chat-config (hybrid: prefix + slash)."""

from __future__ import annotations

import discord
from discord.ext import commands

from bot.config import get_config
from bot.core.services.ai_service import get_ai_service
from .base import check_ai_enabled, check_ai_enabled_interaction, split_message


class ChatCog(commands.Cog):
    """AI Assistant commands for the Discord server."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.config = get_config()
        self.ai_service = get_ai_service()

    @commands.hybrid_command(name="chat", description="Ask the AI assistant", aliases=["ask", "ai"])
    @discord.app_commands.describe(question="Your question for the AI", private="Reply privately (ephemeral)")
    async def chat_command(
        self,
        ctx: commands.Context,
        *,
        question: str,
        private: bool = False,
    ):
        """Ask the AI assistant anything."""
        if not await check_ai_enabled_interaction(ctx):
            return

        await ctx.defer(ephemeral=private)

        response = await self.ai_service.chat(
            guild_id=ctx.guild.id,
            user_id=ctx.author.id,
            user_message=question,
        )

        for chunk in split_message(response):
            await ctx.send(chunk)

    @commands.hybrid_command(name="clear-chat", description="Clear your AI conversation history")
    async def clear_chat_command(self, ctx: commands.Context):
        """Clear your AI conversation history."""
        if not await check_ai_enabled_interaction(ctx):
            return

        self.ai_service.clear_history(ctx.guild.id, ctx.author.id)
        await ctx.send("✅ Your conversation history has been cleared.")

    @commands.hybrid_command(name="chat-config", description="Show current AI configuration")
    async def chat_config_command(self, ctx: commands.Context):
        """Show current AI configuration."""
        if not await check_ai_enabled_interaction(ctx):
            return

        embed = discord.Embed(
            title="🤖 AI Chat Configuration",
            color=discord.Color.blurple(),
        )
        embed.add_field(name="Provider", value=self.config.ai_provider, inline=True)
        embed.add_field(name="Model", value=self.config.ai_default_model, inline=True)
        embed.add_field(name="Max History", value=str(self.config.ai_max_history), inline=True)
        embed.add_field(name="Temperature", value=str(self.config.ai_temperature), inline=True)
        embed.add_field(name="Enabled", value="✅ Yes" if self.config.ai_enabled else "❌ No", inline=True)
        await ctx.send(embed=embed)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(ChatCog(bot))
