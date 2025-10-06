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

__all__ = [
    "theme",
    "set_theme_mode",
    "get_theme_mode",
    "get_console",
    "set_theme",
    "list_available_themes",
    "detect_terminal_mode",
]
