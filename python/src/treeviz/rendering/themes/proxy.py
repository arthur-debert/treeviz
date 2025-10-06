"""
Auto-dispatching theme proxy system for treeviz.

Provides transparent theme switching without rendering code needing
to be theme-aware. The theme proxy automatically resolves to the
correct style based on the current terminal theme.
"""

from typing import Dict, Any, Optional, List
from rich.theme import Theme as RichTheme
from .detector import detect_terminal_mode
from ...config.loaders import create_config_loaders


class StyleProxy:
    """Proxy that auto-resolves to correct style based on current theme."""

    def __init__(self, light_style: str, dark_style: str):
        self._light = light_style
        self._dark = dark_style

    @property
    def style(self) -> str:
        """Returns the Rich style string for current theme."""
        # This checks global theme state (set once at startup)
        return self._dark if _current_mode == "dark" else self._light

    # For direct Rich integration
    def __str__(self) -> str:
        return self.style

    def __repr__(self) -> str:
        return f"StyleProxy(light={self._light!r}, dark={self._dark!r})"


class ThemeProxy:
    """Auto-dispatching theme that resolves styles based on terminal theme."""

    def __init__(self, config: Dict[str, Any]):
        self._styles = {}

        # Build style proxies from clier.config
        for style_name, style_defs in config.get("styles", {}).items():
            if isinstance(style_defs, dict):
                self._styles[style_name] = StyleProxy(
                    light_style=style_defs.get("light", "default"),
                    dark_style=style_defs.get("dark", "default"),
                )
            else:
                # Support simple string styles (same for both modes)
                self._styles[style_name] = StyleProxy(
                    light_style=style_defs, dark_style=style_defs
                )

    def __getattr__(self, name: str) -> StyleProxy:
        """Auto-generate style accessors."""
        if name in self._styles:
            return self._styles[name]
        raise AttributeError(f"No style named '{name}'")

    @property
    def rich_theme(self) -> RichTheme:
        """Generate Rich theme for current mode."""
        return RichTheme(
            {name: str(style) for name, style in self._styles.items()}
        )

    # Short aliases for common access patterns
    @property
    def s(self) -> "ThemeProxy":
        """Short alias for styles (theme.s.primary)."""
        return self


# Global theme state - set once at startup
_current_mode: str = "dark"


def set_theme_mode(mode: Optional[str] = None):
    """Set the global theme mode."""
    global _current_mode
    if mode is None:
        mode = detect_terminal_mode()
    if mode not in ("light", "dark"):
        raise ValueError(
            f"Invalid theme mode: {mode}. Must be 'light' or 'dark'."
        )
    _current_mode = mode


def get_theme_mode() -> str:
    """Get the current theme mode."""
    return _current_mode


# Default theme configuration matching current DARK_THEME/LIGHT_THEME
DEFAULT_THEME_CONFIG = {
    "styles": {
        # Tree structure elements
        "icon": {"light": "#0066CC", "dark": "#66B3FF"},
        "label": {"light": "#000000", "dark": "#FFFFFF"},
        "extras": {"light": "#495057", "dark": "#ADB5BD"},
        "numlines": {"light": "#ADB5BD", "dark": "#6C757D"},
        "position": {"light": "#CED4DA", "dark": "#CED4DA"},
        "type": {"light": "#6600CC", "dark": "#B366FF"},
        # Semantic styles
        "default": {"light": "#000000", "dark": "#FFFFFF"},
        "muted": {"light": "#ADB5BD", "dark": "#6C757D"},
        "subdued": {"light": "#495057", "dark": "#ADB5BD"},
        "faint": {"light": "#CED4DA", "dark": "#CED4DA"},
        "info": {"light": "#0066CC", "dark": "#66B3FF"},
        "emphasis": {"light": "bold #000000", "dark": "bold #FFFFFF"},
        "strong": {"light": "bold #000000", "dark": "bold #FFFFFF"},
        "warning": {"light": "#CC6600", "dark": "#FFB366"},
        "error": {"light": "#CC0000", "dark": "#FF6666"},
        "success": {"light": "#009900", "dark": "#66FF66"},
    }
}


# Initialize config loaders and global theme proxy
_theme_loaders = create_config_loaders()
_theme_config = DEFAULT_THEME_CONFIG

# Try to load default theme from YAML
try:
    theme_obj = _theme_loaders.load_theme("default")
    if theme_obj and theme_obj.styles:
        _theme_config = {"styles": theme_obj.styles}
except Exception:
    # Fall back to hardcoded theme if loading fails
    pass

theme = ThemeProxy(_theme_config)

# Set initial mode based on terminal detection
set_theme_mode()


# Console management
_console_cache: Dict[str, Any] = {}


def get_console(force_terminal: bool = False):
    """Get a Rich console with the current theme applied."""
    from rich.console import Console

    cache_key = f"{_current_mode}_{force_terminal}"

    if cache_key not in _console_cache:
        _console_cache[cache_key] = Console(
            theme=theme.rich_theme, force_terminal=force_terminal
        )

    return _console_cache[cache_key]


def set_theme(theme_name: str):
    """
    Load and set a theme by name.

    Args:
        theme_name: Name of the theme to load

    Raises:
        ValueError: If theme not found or invalid
    """
    global theme, _console_cache

    if theme_name.lower() == "default":
        theme_config = DEFAULT_THEME_CONFIG
    else:
        theme_obj = _theme_loaders.load_theme(theme_name)
        if not theme_obj:
            raise ValueError(f"Theme '{theme_name}' not found")
        # Convert Theme object to dict format for ThemeProxy
        theme_config = {"styles": theme_obj.styles}

    # Create new theme proxy
    theme = ThemeProxy(theme_config)

    # Clear console cache to force recreation with new theme
    _console_cache.clear()


def list_available_themes() -> List[str]:
    """List all available theme names."""
    themes = ["default"]  # Always include default
    themes.extend(_theme_loaders.get_theme_names())
    return list(set(themes))  # Remove duplicates
