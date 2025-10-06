"""
Theme configuration for treeviz.

Provides the Theme dataclass for managing color schemes and styles.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional


@dataclass
class Theme:
    """Theme configuration for treeviz visualization."""

    name: str
    styles: Dict[str, Dict[str, str]] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, config: Dict[str, Any]) -> "Theme":
        """Create Theme from dictionary configuration."""
        return cls(
            name=config.get("name", "custom"), styles=config.get("styles", {})
        )

    def get_style(
        self, style_name: str, is_dark: bool = False
    ) -> Optional[str]:
        """
        Get a style value for the given terminal background.

        Args:
            style_name: Name of the style (e.g., "icon", "label")
            is_dark: Whether the terminal has a dark background

        Returns:
            The style string or None if not found
        """
        if style_name not in self.styles:
            return None

        style_config = self.styles[style_name]
        if isinstance(style_config, str):
            # Simple string style
            return style_config
        elif isinstance(style_config, dict):
            # Light/dark variant
            key = "dark" if is_dark else "light"
            return style_config.get(key)
        return None

    def merge(self, other: "Theme") -> "Theme":
        """Merge with another Theme, with other taking precedence."""
        merged_styles = self.styles.copy()

        # Deep merge styles
        for key, value in other.styles.items():
            if (
                key in merged_styles
                and isinstance(merged_styles[key], dict)
                and isinstance(value, dict)
            ):
                # Merge style dictionaries
                merged_styles[key] = {**merged_styles[key], **value}
            else:
                # Override completely
                merged_styles[key] = value

        return Theme(
            name=other.name if other.name else self.name, styles=merged_styles
        )
