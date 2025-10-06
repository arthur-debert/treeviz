"""
Treeviz theme provider implementation.

Provides themes and style mappings to the clier framework.
"""

from typing import Dict, Optional
from pathlib import Path

from clier.rendering.themes import Theme, ThemeProvider
from ..config.loaders import create_config_loaders


class TreevizThemeProvider(ThemeProvider):
    """Theme provider for treeviz application."""

    def __init__(self):
        """Initialize with treeviz config loaders."""
        self._loaders = create_config_loaders()

        # Load style mapping from config file
        self._style_mapping = self._load_style_mapping()

    def _load_style_mapping(self) -> Dict[str, str]:
        """Load style mapping from styles.yaml."""
        # Try to load from config
        try:
            import yaml

            config_path = (
                Path(__file__).parent.parent / "config" / "styles.yaml"
            )
            if config_path.exists():
                with open(config_path) as f:
                    return yaml.safe_load(f)
        except Exception:
            pass

        # Fallback to defaults
        return {
            # Tree structure elements
            "icon": "accent",
            "label": "primary",
            "extras": "subdued",
            "numlines": "muted",
            "position": "faint",
            "type": "secondary",
            # Keep semantic styles as-is
            "default": "primary",
            "muted": "muted",
            "subdued": "subdued",
            "faint": "faint",
            "info": "info",
            "emphasis": "emphasis",
            "strong": "strong",
            "warning": "warning",
            "error": "error",
            "success": "success",
        }

    def get_theme(self, name: str) -> Optional[Theme]:
        """Load a theme by name."""
        theme_data = self._loaders.load_theme(name)
        if not theme_data:
            return None

        # Check if it's the new format with colors dict
        if hasattr(theme_data, "colors"):
            return Theme(name=theme_data.name, colors=theme_data.colors)
        elif hasattr(theme_data, "styles"):
            # Old format with styles dict - convert it
            colors = {}

            # Create a reverse mapping for conversion
            reverse_mapping = {}
            for style_name, color_name in self._style_mapping.items():
                if color_name not in reverse_mapping:
                    reverse_mapping[color_name] = []
                reverse_mapping[color_name].append(style_name)

            # Convert styles to colors
            for style_name, style_config in theme_data.styles.items():
                # Check if this is a color name directly
                if style_name in reverse_mapping:
                    colors[style_name] = style_config
                else:
                    # Map style to color name
                    color_name = self._style_mapping.get(style_name, style_name)
                    colors[color_name] = style_config

            return Theme(name=theme_data.name, colors=colors)
        else:
            # Unknown format
            return None

    def get_style_mapping(self) -> Dict[str, str]:
        """Get the mapping of style names to color names."""
        return self._style_mapping.copy()

    def list_themes(self) -> list[str]:
        """List available theme names."""
        return self._loaders.get_theme_names()
