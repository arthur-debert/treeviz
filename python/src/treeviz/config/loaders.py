"""
Configuration loaders for 3viz using the ConfigManager.

Provides loaders for themes, adapters, and view configurations.
"""

from typing import List, Optional, Any
from pathlib import Path
from dataclasses import dataclass

from clier.config import ConfigManager, ConfigSpec


@dataclass
class ConfigLoaders:
    """Container for all configuration loaders."""

    manager: ConfigManager

    def __post_init__(self):
        """Register all configuration specifications."""
        # Lazy imports to avoid circular dependencies
        from ..rendering.theme import Theme
        from ..rendering.presentation import ViewOptions
        from ..definitions.model import AdapterDef

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

    def load_all_themes(self) -> List[Any]:
        """Load all available themes."""
        return self.manager.get("themes")

    def load_theme(self, name: str) -> Optional[Any]:
        """Load a specific theme by name."""
        try:
            theme = self.manager.get("theme", params={"name": name})
            # ConfigManager returns empty dict/object if nothing found
            if theme and hasattr(theme, "name"):
                return theme
            return None
        except Exception:
            return None

    def load_all_adapters(self) -> List[Any]:
        """Load all available adapter definitions."""
        return self.manager.get("adapters")

    def load_adapter(self, name: str) -> Optional[Any]:
        """Load a specific adapter by name."""
        try:
            adapter = self.manager.get("adapter", params={"name": name})
            # ConfigManager returns empty dict/object if nothing found
            if adapter and hasattr(adapter, "label"):
                # Populate the name field if not already set
                if not adapter.name:
                    adapter.name = name
                return adapter
            return None
        except Exception:
            return None

    def load_view_options(self) -> Any:
        """Load view configuration with hierarchy merging."""
        return self.manager.get("view")

    def get_theme_names(self) -> List[str]:
        """Get list of available theme names."""
        themes = self.load_all_themes()
        return [theme.name for theme in themes]

    def get_adapter_names(self) -> List[str]:
        """Get list of available adapter names."""
        adapters = self.load_all_adapters()
        return [adapter.name for adapter in adapters if adapter.name]


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
    # Get the treeviz package config directory
    package_config_path = Path(__file__).parent.parent / "config"

    manager = ConfigManager(
        app_name=app_name,
        search_paths=search_paths,
        package_config_path=package_config_path,
    )

    return ConfigLoaders(manager)
