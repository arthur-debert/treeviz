"""
Theme management for treeviz rendering.

This module provides theme definitions and automatic detection
of terminal dark/light mode.
"""

from .proxy import (
    theme,
    set_theme_mode,
    get_theme_mode,
    get_console,
    set_theme,
    list_available_themes,
)
from .detector import detect_terminal_mode

# Legacy exports for backward compatibility during transition
from .definitions import DARK_THEME, LIGHT_THEME
from .manager import ThemeManager, theme_manager

__all__ = [
    # New theme system
    "theme",
    "set_theme_mode",
    "get_theme_mode",
    "get_console",
    "set_theme",
    "list_available_themes",
    "detect_terminal_mode",
    # Legacy (to be removed after full migration)
    "DARK_THEME",
    "LIGHT_THEME",
    "ThemeManager",
    "theme_manager",
]
