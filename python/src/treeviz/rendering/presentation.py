"""
Presentation configuration for treeviz.

Provides a unified configuration system for all visual aspects including
themes, icons, view options, and output formats.
"""

from dataclasses import dataclass, field, asdict
import enum
from typing import Dict, Any, Union, Optional
from pathlib import Path
from ruamel.yaml import YAML
from ..const import ICONS


class ShowTypes(enum.StrEnum):
    """When to show node type information."""

    NEVER = "never"
    ALWAYS = "always"
    MISSING = "missing"  # Only show if no icon


class CompactMode(enum.StrEnum):
    """How to handle repetitive content."""

    OFF = "off"  # Default, show all
    HIDE = "hide"  # Hide identical inner lines
    DITTO = "ditto"  # Show ditto mark for repeated labels


@dataclass
class ViewOptions:
    """Visual rendering options that control output appearance."""

    max_width: int = 120  # -1 means use terminal width
    show_line_count: bool = True  # Show content line count (e.g., "3L")
    show_types: ShowTypes = ShowTypes.ALWAYS  # When to show node types
    show_extras: bool = True  # Show extra metadata
    show_positions: bool = False  # Show source positions (not implemented)
    compact_mode: CompactMode = CompactMode.OFF  # Handle repetitive content
    """ Some cases for example have paragpagh, single line, then a text element inside. This restults in 3 lines with the same text.  Compact mode can be :
        - None:  default, off
        - hide: hide identical inner lines
        - ditto: following nodes wil show the ditto mark for label

    ¶ More content here.                                      1L
      ↵ "                                                     1L
         ◦  "                                                 1L
    """
    show_tree_guides: bool = True  # Show tree guide lines
    indent_size: int = 2

    @classmethod
    def from_dict(cls, config: Dict[str, Any]) -> "ViewOptions":
        """Create ViewOptions from dictionary, converting strings to enums."""
        config = config.copy()  # Don't modify original

        # Convert string values to enums if needed
        if "show_types" in config and isinstance(config["show_types"], str):
            config["show_types"] = ShowTypes(config["show_types"])

        if "compact_mode" in config and isinstance(config["compact_mode"], str):
            config["compact_mode"] = CompactMode(config["compact_mode"])

        return cls(**config)

    def merge(self, other: "ViewOptions") -> "ViewOptions":
        """Merge with another ViewOptions, with other taking precedence."""
        result_dict = asdict(self)
        other_dict = asdict(other)

        # Update only non-None values
        for key, value in other_dict.items():
            if value is not None:
                result_dict[key] = value

        return ViewOptions.from_dict(result_dict)


@dataclass
class Presentation:
    """Complete presentation configuration for treeviz visualization."""

    theme: str = "default"  # Theme name to be resolved
    icon_pack: str = "treeviz"  # Icon pack name to be resolved
    icons: Dict[str, str] = field(
        default_factory=lambda: ICONS.copy()
    )  # Direct icon overrides
    view: ViewOptions = field(default_factory=ViewOptions)

    @classmethod
    def from_dict(cls, config: Dict[str, Any]) -> "Presentation":
        """Create Presentation from a dictionary configuration."""
        # Extract nested options
        view_config = config.get("view", {})

        # Create sub-options using ViewOptions.from_dict
        view = (
            ViewOptions.from_dict(view_config) if view_config else ViewOptions()
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

        # Merge view options
        view = self.view.merge(other.view)

        return Presentation(
            theme=theme,
            icon_pack=icon_pack,
            icons=icons,
            view=view,
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        view_dict = asdict(self.view)
        # Convert enums to strings for serialization
        if isinstance(view_dict.get("show_types"), ShowTypes):
            view_dict["show_types"] = view_dict["show_types"].value
        if isinstance(view_dict.get("compact_mode"), CompactMode):
            view_dict["compact_mode"] = view_dict["compact_mode"].value

        return {
            "theme": self.theme,
            "icon_pack": self.icon_pack,
            "icons": self.icons,
            "view": view_dict,
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
