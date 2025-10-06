"""
Base theme types and interfaces for clier.

Provides the core theme abstractions that applications can implement.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, Optional


@dataclass
class Theme:
    """Base theme with color definitions."""

    name: str
    colors: Dict[
        str, Dict[str, str]
    ]  # color_name -> {light: "#hex", dark: "#hex"}

    def get_color(
        self, color_name: str, is_dark: bool = False
    ) -> Optional[str]:
        """Get a color value for the given terminal background."""
        if color_name not in self.colors:
            return None

        color_config = self.colors[color_name]
        if isinstance(color_config, str):
            # Simple string color
            return color_config
        elif isinstance(color_config, dict):
            # Light/dark variant
            key = "dark" if is_dark else "light"
            return color_config.get(key)
        return None


class ThemeProvider(ABC):
    """Interface for providing themes to the framework."""

    @abstractmethod
    def get_theme(self, name: str) -> Optional[Theme]:
        """Load a theme by name."""
        pass

    @abstractmethod
    def get_style_mapping(self) -> Dict[str, str]:
        """Get the mapping of style names to color names."""
        pass

    @abstractmethod
    def list_themes(self) -> list[str]:
        """List available theme names."""
        pass
