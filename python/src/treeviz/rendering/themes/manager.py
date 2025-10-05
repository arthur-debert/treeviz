"""
Theme manager for treeviz rendering.

Provides a singleton-like manager for handling themes and Rich console creation.
"""

from typing import Optional, Literal, Dict, Any
from rich.console import Console
from rich.theme import Theme

from .definitions import DARK_THEME, LIGHT_THEME
from .detector import detect_terminal_mode


class ThemeManager:
    """
    Manages theme selection and Rich console creation.

    Use the module-level `theme_manager` instance instead of creating new instances.
    """

    def __init__(self):
        """Initialize the theme manager."""
        self._console_cache: Dict[str, Console] = {}
        self.active_mode: Literal["dark", "light"] = detect_terminal_mode()
        self.active_theme: Theme = (
            DARK_THEME if self.active_mode == "dark" else LIGHT_THEME
        )
        self._custom_themes: Dict[str, Theme] = {}

    def set_mode(self, mode: Literal["dark", "light"]) -> None:
        """
        Manually set the theme mode.

        Args:
            mode: 'dark' or 'light'
        """
        self.active_mode = mode
        self.active_theme = DARK_THEME if mode == "dark" else LIGHT_THEME
        # Clear console cache when theme changes
        self._console_cache.clear()

    def register_theme(self, name: str, theme: Theme) -> None:
        """
        Register a custom theme.

        Args:
            name: Theme name
            theme: Rich Theme object
        """
        self._custom_themes[name] = theme

    def set_theme(self, theme_name: str) -> None:
        """
        Set the active theme by name.

        Args:
            theme_name: Name of registered theme or 'dark'/'light'
        """
        if theme_name == "dark":
            self.active_theme = DARK_THEME
            self.active_mode = "dark"
        elif theme_name == "light":
            self.active_theme = LIGHT_THEME
            self.active_mode = "light"
        elif theme_name in self._custom_themes:
            self.active_theme = self._custom_themes[theme_name]
            # Keep current mode for custom themes
        else:
            raise ValueError(f"Unknown theme: {theme_name}")

        # Clear console cache when theme changes
        self._console_cache.clear()

    def get_console(
        self,
        force_terminal: Optional[bool] = None,
        no_color: bool = False,
        width: Optional[int] = None,
        **kwargs: Any,
    ) -> Console:
        """
        Get a Rich Console configured with the active theme.

        Args:
            force_terminal: Force terminal mode
            no_color: Disable colors
            width: Console width
            **kwargs: Additional Console parameters

        Returns:
            Configured Rich Console
        """
        # Create cache key from parameters
        cache_key = f"{force_terminal}_{no_color}_{width}"

        # Return cached console if available
        if cache_key in self._console_cache:
            return self._console_cache[cache_key]

        # Create new console
        console = Console(
            theme=self.active_theme if not no_color else None,
            force_terminal=force_terminal,
            no_color=no_color,
            width=width,
            **kwargs,
        )

        # Cache for reuse
        self._console_cache[cache_key] = console

        return console

    def get_style(self, style_name: str) -> str:
        """
        Get the color/style value for a semantic style name.

        Args:
            style_name: Semantic style name (e.g., 'icon', 'label')

        Returns:
            Style string or empty string if not found
        """
        if self.active_theme and style_name in self.active_theme.styles:
            return str(self.active_theme.styles[style_name])
        return ""

    def reset(self) -> None:
        """Reset the theme manager state (mainly for testing)."""
        self._console_cache.clear()
        self.active_mode = detect_terminal_mode()
        self.active_theme = (
            DARK_THEME if self.active_mode == "dark" else LIGHT_THEME
        )
        self._custom_themes.clear()


# Create the singleton instance at module level
theme_manager = ThemeManager()
