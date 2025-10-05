"""
Theme management for treeviz rendering.

This module provides theme definitions and automatic detection
of terminal dark/light mode.
"""

from .definitions import DARK_THEME, LIGHT_THEME
from .detector import detect_terminal_mode
from .manager import ThemeManager, theme_manager

__all__ = ["DARK_THEME", "LIGHT_THEME", "detect_terminal_mode", "ThemeManager", "theme_manager"]
