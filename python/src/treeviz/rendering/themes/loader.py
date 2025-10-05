"""
Theme loading utilities for treeviz.

Loads themes from YAML files and provides discovery mechanisms.
"""

from ruamel.yaml import YAML
from pathlib import Path
from typing import Dict, Any, List
import importlib.resources


class ThemeLoader:
    """Handles loading and discovery of themes."""

    def __init__(self):
        self._theme_cache: Dict[str, Dict[str, Any]] = {}
        self._theme_paths: List[Path] = []
        self._yaml = YAML()
        self._yaml.preserve_quotes = True
        self._initialize_paths()

    def _initialize_paths(self):
        """Initialize theme search paths."""
        # 1. Package-bundled themes (highest priority)
        try:
            if hasattr(importlib.resources, "files"):
                # Python 3.9+
                themes_package = importlib.resources.files("treeviz.themes")
                if themes_package.is_dir():
                    self._theme_paths.append(themes_package)
            else:
                # Python 3.8
                with importlib.resources.path(
                    "treeviz.themes", "__init__.py"
                ) as init_path:
                    themes_dir = init_path.parent
                    if themes_dir.exists():
                        self._theme_paths.append(themes_dir)
        except Exception:
            pass

        # 2. User config directory
        user_config = Path.home() / ".config" / "3viz" / "themes"
        if user_config.exists():
            self._theme_paths.append(user_config)

        # 3. Alternative user directory
        user_alt = Path.home() / ".3viz" / "themes"
        if user_alt.exists():
            self._theme_paths.append(user_alt)

        # 4. Project local themes
        local_themes = Path(".3viz") / "themes"
        if local_themes.exists():
            self._theme_paths.append(local_themes)

    def load_theme(self, name: str) -> Dict[str, Any]:
        """
        Load a theme by name.

        Args:
            name: Theme name (without .yaml extension)

        Returns:
            Theme configuration dictionary

        Raises:
            ValueError: If theme not found
        """
        # Check cache first
        if name in self._theme_cache:
            return self._theme_cache[name]

        # Search for theme file
        for theme_path in self._theme_paths:
            theme_file = theme_path / f"{name}.yaml"

            # Handle both Path objects and traversable objects (importlib.resources)
            if hasattr(theme_file, "read_text"):
                # importlib.resources traversable
                try:
                    content = theme_file.read_text()
                    theme_config = self._yaml.load(content)
                    self._theme_cache[name] = theme_config
                    return theme_config
                except Exception:
                    continue
            elif isinstance(theme_file, Path) and theme_file.exists():
                # Regular Path
                with open(theme_file, "r") as f:
                    theme_config = self._yaml.load(f)
                    self._theme_cache[name] = theme_config
                    return theme_config

        raise ValueError(f"Theme '{name}' not found in any theme directory")

    def list_themes(self) -> List[str]:
        """
        List all available themes.

        Returns:
            List of theme names
        """
        themes = set()

        for theme_path in self._theme_paths:
            # Handle both Path objects and traversable objects
            if hasattr(theme_path, "iterdir"):
                try:
                    for item in theme_path.iterdir():
                        if hasattr(item, "name") and item.name.endswith(
                            ".yaml"
                        ):
                            theme_name = item.name[:-5]  # Remove .yaml
                            themes.add(theme_name)
                except Exception:
                    continue
            elif isinstance(theme_path, Path):
                for yaml_file in theme_path.glob("*.yaml"):
                    theme_name = yaml_file.stem
                    themes.add(theme_name)

        return sorted(list(themes))

    def validate_theme(self, theme_config: Dict[str, Any]) -> bool:
        """
        Validate theme configuration structure.

        Args:
            theme_config: Theme configuration to validate

        Returns:
            True if valid, raises ValueError otherwise
        """
        if not isinstance(theme_config, dict):
            raise ValueError("Theme must be a dictionary")

        if "styles" not in theme_config:
            raise ValueError("Theme must contain 'styles' key")

        styles = theme_config["styles"]
        if not isinstance(styles, dict):
            raise ValueError("'styles' must be a dictionary")

        # Check that each style has light/dark or is a string
        for style_name, style_def in styles.items():
            if isinstance(style_def, str):
                # Simple string style is valid
                continue
            elif isinstance(style_def, dict):
                if "light" not in style_def or "dark" not in style_def:
                    raise ValueError(
                        f"Style '{style_name}' must have both 'light' and 'dark' keys"
                    )
            else:
                raise ValueError(
                    f"Style '{style_name}' must be a string or dictionary"
                )

        return True


# Global theme loader instance
theme_loader = ThemeLoader()


def load_theme(name: str) -> Dict[str, Any]:
    """Load a theme by name."""
    return theme_loader.load_theme(name)


def list_themes() -> List[str]:
    """List all available themes."""
    return theme_loader.list_themes()


def validate_theme(theme_config: Dict[str, Any]) -> bool:
    """Validate theme configuration."""
    return theme_loader.validate_theme(theme_config)
