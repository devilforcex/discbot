"""Facade for backward compatibility — actual code in bot/music/help/ package."""

from .help import (
    CATEGORIES,
    HelpCategorySelect,
    HelpView,
    build_category_embed,
    build_main_help_embed,
)

__all__ = [
    "CATEGORIES",
    "HelpView",
    "HelpCategorySelect",
    "build_main_help_embed",
    "build_category_embed",
]
