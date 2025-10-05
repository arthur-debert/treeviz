"""
Configuration loaders for 3viz using the ConfigManager.

Provides loaders for themes, adapters, and view configurations.
"""

from typing import List, Optional
from pathlib import Path
from dataclasses import dataclass

from config import ConfigManager, ConfigSpec
from ..rendering.theme import Theme
from ..rendering.presentation import ViewOptions
from ..definitions.model import AdapterDef


@dataclass
class ConfigLoaders:
    """Container for all configuration loaders."""

    manager: ConfigManager

    def __post_init__(self):
        """Register all configuration specifications."""
        # Theme configurations
        self.manager.register(
            ConfigSpec(
                name="themes",
                pattern="themes/*.yaml",
                collection=True,
                dataclass=Theme,
            )
        )

        # Single theme by name
        self.manager.register(
            ConfigSpec(
                name="theme",
                pattern="themes/{name}.yaml",
                collection=False,
                dataclass=Theme,
            )
        )

        # Adapter configurations
        self.manager.register(
            ConfigSpec(
                name="adapters",
                pattern="adapters/*.yaml",
                collection=True,
                dataclass=AdapterDef,
            )
        )

        # Single adapter by name
        self.manager.register(
            ConfigSpec(
                name="adapter",
                pattern="adapters/{name}.yaml",
                collection=False,
                dataclass=AdapterDef,
            )
        )

        # View configuration
        self.manager.register(
            ConfigSpec(
                name="view",
                pattern="view.yaml",
                collection=False,
                merge=True,
                dataclass=ViewOptions,
            )
        )

    def load_all_themes(self) -> List[Theme]:
        """Load all available themes."""
        return self.manager.get("themes")

    def load_theme(self, name: str) -> Optional[Theme]:
        """Load a specific theme by name."""
        # Temporarily update the pattern with the actual name
        spec = self.manager.specs["theme"]
        original_pattern = spec.pattern
        spec.pattern = f"themes/{name}.yaml"

        try:
            theme_data = self.manager.get("theme", force_reload=True)
            if theme_data:
                return theme_data
        finally:
            # Restore original pattern
            spec.pattern = original_pattern

        return None

    def load_all_adapters(self) -> List[AdapterDef]:
        """Load all available adapter definitions."""
        return self.manager.get("adapters")

    def load_adapter(self, name: str) -> Optional[AdapterDef]:
        """Load a specific adapter by name."""
        # Temporarily update the pattern with the actual name
        spec = self.manager.specs["adapter"]
        original_pattern = spec.pattern
        spec.pattern = f"adapters/{name}.yaml"

        try:
            adapter_data = self.manager.get("adapter", force_reload=True)
            if adapter_data:
                return adapter_data
        finally:
            # Restore original pattern
            spec.pattern = original_pattern

        return None

    def load_view_options(self) -> ViewOptions:
        """Load view configuration with hierarchy merging."""
        return self.manager.get("view")

    def get_theme_names(self) -> List[str]:
        """Get list of available theme names."""
        themes = self.load_all_themes()
        return [theme.name for theme in themes]

    def get_adapter_names(self) -> List[str]:
        """Get list of available adapter names."""
        adapters = self.load_all_adapters()
        return [
            adapter.name for adapter in adapters if hasattr(adapter, "name")
        ]


def create_config_loaders(
    search_paths: Optional[List[Path]] = None, app_name: str = "3viz"
) -> ConfigLoaders:
    """
    Create configured loaders for the application.

    Args:
        search_paths: Optional explicit search paths
        app_name: Application name for config directories

    Returns:
        ConfigLoaders instance ready to use
    """
    manager = ConfigManager(app_name=app_name, search_paths=search_paths)

    return ConfigLoaders(manager)
