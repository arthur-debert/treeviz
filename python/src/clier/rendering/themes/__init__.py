"""
Theme management for clier rendering framework.

This module provides theme definitions and automatic detection
of terminal dark/light mode.
"""

from .base import Theme, ThemeProvider
from .proxy import (
    theme,
    set_theme_mode,
    get_theme_mode,
    get_console,
    set_theme,
    list_available_themes,
    set_theme_provider,
)
from .detector import detect_terminal_mode

__all__ = [
    "Theme",
    "ThemeProvider",
    "theme",
    "set_theme_mode",
    "get_theme_mode",
    "get_console",
    "set_theme",
    "list_available_themes",
    "set_theme_provider",
    "detect_terminal_mode",
]
