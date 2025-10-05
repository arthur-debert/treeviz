"""
Rendering options for treeviz.

Provides a unified configuration system for themes, icon packs,
and view options.
"""

from dataclasses import dataclass, field, asdict
from typing import Dict, Any, Union, Optional
from pathlib import Path
from ruamel.yaml import YAML


@dataclass
class ViewOptions:
    """Visual rendering options that control output appearance."""

    max_width: int = 120
    show_line_numbers: bool = True
    show_types: bool = True
    show_extras: bool = True
    show_positions: bool = False
    compact_mode: bool = False
    indent_size: int = 2
    tree_guides: bool = True
    color_output: str = "auto"  # auto, always, never

    def merge(self, other: "ViewOptions") -> "ViewOptions":
        """Merge with another ViewOptions, with other taking precedence."""
        result_dict = asdict(self)
        other_dict = asdict(other)

        # Update only non-None values
        for key, value in other_dict.items():
            if value is not None:
                result_dict[key] = value

        return ViewOptions(**result_dict)


@dataclass
class OutputOptions:
    """Output format options."""

    format: str = "tree"  # tree, flat, json
    syntax_highlight: bool = True

    def merge(self, other: "OutputOptions") -> "OutputOptions":
        """Merge with another OutputOptions, with other taking precedence."""
        result_dict = asdict(self)
        other_dict = asdict(other)

        for key, value in other_dict.items():
            if value is not None:
                result_dict[key] = value

        return OutputOptions(**result_dict)


@dataclass
class RenderingOptions:
    """Complete rendering configuration including theme, icons, and view options."""

    theme: Union[str, Dict[str, Any]] = "default"
    icon_pack: Union[str, Dict[str, Any]] = "treeviz"
    view: ViewOptions = field(default_factory=ViewOptions)
    output: OutputOptions = field(default_factory=OutputOptions)

    @classmethod
    def from_dict(cls, config: Dict[str, Any]) -> "RenderingOptions":
        """Create RenderingOptions from a dictionary configuration."""
        # Extract nested options
        view_config = config.get("view", {})
        output_config = config.get("output", {})

        # Create sub-options
        view = ViewOptions(**view_config) if view_config else ViewOptions()
        output = (
            OutputOptions(**output_config) if output_config else OutputOptions()
        )

        # Create main options
        return cls(
            theme=config.get("theme", "default"),
            icon_pack=config.get("icon_pack", "treeviz"),
            view=view,
            output=output,
        )

    @classmethod
    def from_yaml(cls, path: Union[str, Path]) -> "RenderingOptions":
        """Load RenderingOptions from a YAML file."""
        yaml = YAML()
        yaml.preserve_quotes = True

        path = Path(path)
        with open(path, "r") as f:
            config = yaml.load(f)

        return cls.from_dict(config)

    def merge(self, other: "RenderingOptions") -> "RenderingOptions":
        """
        Merge with another RenderingOptions, with other taking precedence.

        This allows for configuration layering:
        1. Default options
        2. User options
        3. Project options
        4. Command-line options
        """
        # Merge theme (other takes precedence if not default)
        theme = other.theme if other.theme != "default" else self.theme

        # Merge icon pack
        icon_pack = (
            other.icon_pack if other.icon_pack != "treeviz" else self.icon_pack
        )

        # Merge view and output options
        view = self.view.merge(other.view)
        output = self.output.merge(other.output)

        return RenderingOptions(
            theme=theme, icon_pack=icon_pack, view=view, output=output
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "theme": self.theme,
            "icon_pack": self.icon_pack,
            "view": asdict(self.view),
            "output": asdict(self.output),
        }


class StyleLoader:
    """Handles loading and merging of style configurations."""

    def __init__(self):
        self.yaml = YAML()
        self.yaml.preserve_quotes = True

    def load_style_hierarchy(
        self, explicit_file: Optional[Path] = None
    ) -> RenderingOptions:
        """
        Load and merge styles from the configuration hierarchy.

        Order (later overrides earlier):
        1. Built-in defaults
        2. User defaults (~/.config/3viz/style.yaml)
        3. Project defaults (./.3viz/style.yaml)
        4. Explicit file (if provided)
        """
        # Start with built-in defaults
        options = RenderingOptions()

        # User defaults
        user_style = Path.home() / ".config" / "3viz" / "style.yaml"
        if user_style.exists():
            try:
                user_options = RenderingOptions.from_yaml(user_style)
                options = options.merge(user_options)
            except Exception:
                # Ignore errors in user config
                pass

        # Alternative user location
        user_alt = Path.home() / ".3viz" / "style.yaml"
        if user_alt.exists():
            try:
                user_options = RenderingOptions.from_yaml(user_alt)
                options = options.merge(user_options)
            except Exception:
                pass

        # Project defaults
        project_style = Path(".3viz") / "style.yaml"
        if project_style.exists():
            try:
                project_options = RenderingOptions.from_yaml(project_style)
                options = options.merge(project_options)
            except Exception:
                pass

        # Explicit file
        if explicit_file:
            explicit_options = RenderingOptions.from_yaml(explicit_file)
            options = options.merge(explicit_options)

        return options

    def apply_overrides(
        self, options: RenderingOptions, overrides: Dict[str, Any]
    ) -> RenderingOptions:
        """
        Apply command-line or API overrides to options.

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

        # Create options from overrides and merge
        override_options = RenderingOptions.from_dict(nested)
        return options.merge(override_options)
