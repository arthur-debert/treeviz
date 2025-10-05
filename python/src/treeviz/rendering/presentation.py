"""
Presentation configuration for treeviz.

Provides a unified configuration system for all visual aspects including
themes, icons, view options, and output formats.
"""

from dataclasses import dataclass, field, asdict
from typing import Dict, Any, Union, Optional
from pathlib import Path
from ruamel.yaml import YAML
from ..const import ICONS


@dataclass
class ViewOptions:
    """Visual rendering options that control output appearance."""

    max_width: int = 120
    """ -1 mans use terminal width"""
    show_line_count: bool = True
    """ this is the num lines of content, not the v index"""
    show_types: bool = True
    """ This can be: "never", "always", "missing", which only shows types if node has no icon"""
    show_extras: bool = True
    show_positions: bool = False  # not implemented
    compact_mode: str | None = None  # not implemented
    """ Some cases for example have paragpagh, single line, then a text element inside. This restults in 3 lines with the same text.  Compact mode can be :
        - None:  default, off
        - hide: hide identical inner lines
        - ditto: following nodes wil show the ditto mark for label

    ¶ More content here.                                      1L
      ↵ "                                                     1L
         ◦  "                                                 1L
    """
    show_tree_guides: bool = True
    """ Show tree guide lines """
    color_output: str = "auto"  # auto, always, never
    indent_size: int = 2

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
class Presentation:
    """Complete presentation configuration for treeviz visualization."""

    theme: Union[str, Dict[str, Any]] = "default"
    icon_pack: Union[str, Dict[str, Any]] = "treeviz"
    icons: Dict[str, str] = field(
        default_factory=lambda: ICONS.copy()
    )  # Direct icon overrides
    view: ViewOptions = field(default_factory=ViewOptions)
    output: OutputOptions = field(default_factory=OutputOptions)

    @classmethod
    def from_dict(cls, config: Dict[str, Any]) -> "Presentation":
        """Create Presentation from a dictionary configuration."""
        # Extract nested options
        view_config = config.get("view", {})
        output_config = config.get("output", {})

        # Create sub-options
        view = ViewOptions(**view_config) if view_config else ViewOptions()
        output = (
            OutputOptions(**output_config) if output_config else OutputOptions()
        )

        # Handle icons - merge with defaults
        icons = ICONS.copy()
        icons.update(config.get("icons", {}))

        # Create main options
        return cls(
            theme=config.get("theme", "default"),
            icon_pack=config.get("icon_pack", "treeviz"),
            icons=icons,
            view=view,
            output=output,
        )

    @classmethod
    def from_yaml(cls, path: Union[str, Path]) -> "Presentation":
        """Load Presentation from a YAML file."""
        yaml = YAML()
        yaml.preserve_quotes = True

        path = Path(path)
        with open(path, "r") as f:
            config = yaml.load(f)

        return cls.from_dict(config)

    def merge(self, other: "Presentation") -> "Presentation":
        """
        Merge with another Presentation, with other taking precedence.

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

        # Merge icons (combine dictionaries, other takes precedence)
        icons = self.icons.copy()
        icons.update(other.icons)

        # Merge view and output options
        view = self.view.merge(other.view)
        output = self.output.merge(other.output)

        return Presentation(
            theme=theme,
            icon_pack=icon_pack,
            icons=icons,
            view=view,
            output=output,
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "theme": self.theme,
            "icon_pack": self.icon_pack,
            "icons": self.icons,
            "view": asdict(self.view),
            "output": asdict(self.output),
        }


class PresentationLoader:
    """Handles loading and merging of presentation configurations."""

    def __init__(self):
        self.yaml = YAML()
        self.yaml.preserve_quotes = True

    def load_presentation_hierarchy(
        self, explicit_file: Optional[Path] = None
    ) -> Presentation:
        """
        Load and merge presentation configurations from the hierarchy.

        Order (later overrides earlier):
        1. Built-in defaults
        2. User defaults (~/.config/3viz/style.yaml)
        3. Project defaults (./.3viz/style.yaml)
        4. Explicit file (if provided)
        """
        # Start with built-in defaults
        options = Presentation()

        # User defaults
        user_presentation = (
            Path.home() / ".config" / "3viz" / "presentation.yaml"
        )
        if user_presentation.exists():
            try:
                user_options = Presentation.from_yaml(user_presentation)
                options = options.merge(user_options)
            except Exception:
                # Ignore errors in user config
                pass

        # Alternative user location
        user_alt = Path.home() / ".3viz" / "presentation.yaml"
        if user_alt.exists():
            try:
                user_options = Presentation.from_yaml(user_alt)
                options = options.merge(user_options)
            except Exception:
                pass

        # Project defaults
        project_presentation = Path(".3viz") / "presentation.yaml"
        if project_presentation.exists():
            try:
                project_options = Presentation.from_yaml(project_presentation)
                options = options.merge(project_options)
            except Exception:
                pass

        # Explicit file
        if explicit_file:
            explicit_options = Presentation.from_yaml(explicit_file)
            options = options.merge(explicit_options)

        return options

    def apply_overrides(
        self, options: Presentation, overrides: Dict[str, Any]
    ) -> Presentation:
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
        override_options = Presentation.from_dict(nested)
        return options.merge(override_options)
