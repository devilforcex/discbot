"""Help package facade — preserves old import path bot.music.help_views."""

from .categories import CATEGORIES, total_categories, total_commands
from .embeds import build_category_embed, build_main_help_embed
from .views import HelpCategorySelect, HelpView

__all__ = [
    "CATEGORIES",
    "total_commands",
    "total_categories",
    "build_main_help_embed",
    "build_category_embed",
    "HelpCategorySelect",
    "HelpView",
]

# Private aliases used internally previously
_total_commands = total_commands
_total_categories = total_categories
