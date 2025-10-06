"""
Presentation configuration loading using the new ConfigLoaders system.
"""

from typing import Optional, Dict, Any
from pathlib import Path
from .presentation import Presentation
from ..config.loaders import create_config_loaders


class PresentationLoader:
    """Handles loading and merging of presentation configurations using ConfigLoaders."""

    def __init__(self):
        self._loaders = create_config_loaders()

    def load_presentation_hierarchy(
        self, explicit_file: Optional[Path] = None
    ) -> Presentation:
        """
        Load and merge presentation configurations from the hierarchy.

        Order (later overrides earlier):
        1. Built-in defaults
        2. User/system view configuration
        3. Project view configuration
        4. Explicit file (if provided)

        Theme is loaded separately based on theme_name.
        """
        # Start with built-in defaults
        presentation = Presentation()

        # Load view options from hierarchy
        view_options = self._loaders.load_view_options()
        presentation.view = view_options

        # If explicit file provided, load it
        if explicit_file:
            # For now, we'll use the old YAML loading for explicit files
            # In a full implementation, this would use ConfigManager too
            explicit_presentation = Presentation.from_yaml(explicit_file)
            presentation = presentation.merge(explicit_presentation)

        # Load the theme based on theme_name
        if presentation.theme_name:
            theme_obj = self._loaders.load_theme(presentation.theme_name)
            if theme_obj:
                presentation.theme = theme_obj

        return presentation

    def apply_overrides(
        self, presentation: Presentation, overrides: Dict[str, Any]
    ) -> Presentation:
        """
        Apply command-line or API overrides to presentation.

        Supports dotted notation: {"view.max_width": 80}
        """
        # Convert dotted keys to nested dict
        nested = {}
        for key, value in overrides.items():
            parts = key.split(".")
            current = nested

            for part in parts[:-1]:
                if part not in current:
                    current[part] = {}
                current = current[part]

            current[parts[-1]] = value

        # Create presentation from overrides and merge
        override_presentation = Presentation.from_dict(nested)
        result = presentation.merge(override_presentation)

        # If theme was changed, reload it
        if "theme" in nested and result.theme_name != presentation.theme_name:
            theme_obj = self._loaders.load_theme(result.theme_name)
            if theme_obj:
                result.theme = theme_obj

        return result
