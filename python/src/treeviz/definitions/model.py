"""
AdapterDef schema for treeviz using dataclasses.

This module provides a clean, typed interface for treeviz definitions
replacing the ad-hoc dictionary validation.
"""

from dataclasses import dataclass, field, asdict
from typing import Dict, List, Any, Union
import fnmatch
from ..const import ICONS
from ..icon_pack import Icon, IconPack, register_icon_pack


@dataclass
class ChildrenSelector:
    """
    Node-based children selection using include/exclude patterns.

    When children are not in a specific attribute but are nodes themselves,
    this selector allows filtering which node types should be considered children.
    """

    include: List[str] = field(
        default_factory=lambda: ["*"],
        metadata={
            "doc": "Node types to include as children (supports '*' wildcard)"
        },
    )
    exclude: List[str] = field(
        default_factory=list,
        metadata={
            "doc": "Node types to exclude from children (supports '*' wildcard)"
        },
    )

    def matches(self, node_type: str) -> bool:
        """
        Check if a node type should be included as a child.

        Args:
            node_type: The type of the node to check

        Returns:
            True if the node should be included as a child
        """
        if not node_type:
            return False

        # Check if included by any include pattern
        included = any(
            fnmatch.fnmatch(node_type, pattern) for pattern in self.include
        )

        if not included:
            return False

        # Check if excluded by any exclude pattern
        excluded = any(
            fnmatch.fnmatch(node_type, pattern) for pattern in self.exclude
        )

        return not excluded


@dataclass
class AdapterDef:
    """
    Treeviz definition schema.

    A clean, typed representation of how to adapt AST nodes to treeviz format.
    """

    # Core extraction mappings (flattened from attributes)
    label: str = field(
        default="label",
        metadata={
            "doc": "Field name to extract node label from (e.g., 'name', 'content', 'title')"
        },
    )
    type: str = field(
        default="type",
        metadata={
            "doc": "Field name to extract node type from (e.g., 'node_type', 'kind', 'tag')"
        },
    )
    children: Union[str, ChildrenSelector] = field(
        default="children",
        metadata={
            "doc": "Field name to extract child nodes from (e.g., 'children', 'body', 'content') or ChildrenSelector for node-based filtering"
        },
    )

    # Optional extraction mappings
    icon: Any = field(
        default=None,
        metadata={
            "doc": "Field name for custom icon extraction, or None to use type-based icons"
        },
    )
    content_lines: Any = field(
        default=1,
        metadata={
            "doc": "Field name for line count extraction, or integer for fixed line count"
        },
    )
    source_location: Any = field(
        default=None,
        metadata={
            "doc": "Field name for source location info (line/column numbers)"
        },
    )
    extra: Any = field(
        default_factory=dict,
        metadata={
            "doc": "Field name for additional extra extraction, or dict for static extra"
        },
    )

    # Optional: Icon mappings (defaults to baseline from const.py)
    icons: Dict[str, str] = field(
        default_factory=lambda: ICONS.copy(),
        metadata={
            "doc": "Mapping from node types to Unicode icons for display"
        },
    )

    # Optional: User-defined icon packs
    icon_packs: List[Dict[str, Any]] = field(
        default_factory=list,
        metadata={"doc": "List of custom icon packs to register for this adapter (uses ICON_PACKS key)"},
    )

    # Optional: Per-type attribute overrides
    type_overrides: Dict[str, Dict[str, str]] = field(
        default_factory=dict,
        metadata={
            "doc": "Per-type field overrides (e.g., {'paragraph': {'label': 'content'}})"
        },
    )

    # Optional: Node types to skip during conversion
    ignore_types: List[str] = field(
        default_factory=list,
        metadata={"doc": "List of node types to skip during tree traversal"},
    )

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AdapterDef":
        """Create AdapterDef from dictionary by merging with defaults."""
        # Handle icon packs registration from "ICON_PACKS" key
        if "ICON_PACKS" in data:
            for pack_data in data.get("ICON_PACKS", []):
                if not isinstance(pack_data, dict) or "name" not in pack_data or "icons" not in pack_data:
                    raise ValueError(f"Invalid icon pack definition: {pack_data}")

                icons = {}
                for icon_name, icon_def in pack_data.get("icons", {}).items():
                    if isinstance(icon_def, dict) and "icon" in icon_def:
                        if not icon_name.isidentifier():
                            raise ValueError(f"Icon name '{icon_name}' is not a valid identifier.")
                        icons[icon_name] = Icon(
                            icon=icon_def.get("icon", "?"),
                            aliases=icon_def.get("aliases", [])
                        )
                    else:
                        raise ValueError(f"Invalid icon definition for '{icon_name}': {icon_def}")

                pack_name = pack_data["name"]
                if not pack_name.isidentifier() or "." in pack_name:
                    raise ValueError(f"Icon pack name '{pack_name}' is not valid.")

                icon_pack = IconPack(name=pack_name, icons=icons)
                register_icon_pack(icon_pack)

        # Start with default definition
        default = cls.default()
        merged_data = asdict(default)

        # Create a clean data copy for merging, mapping ICON_PACKS to icon_packs
        data_for_merging = data.copy()
        if 'ICON_PACKS' in data_for_merging:
            data_for_merging['icon_packs'] = data_for_merging.pop('ICON_PACKS')

        # Simple merge: user data overrides defaults
        for key, value in data_for_merging.items():
            if (
                key == "icons"
                and isinstance(merged_data[key], dict)
                and isinstance(value, dict)
            ):
                # For icons only, merge with baseline (special case)
                merged_data[key].update(value)
            elif (
                key == "children"
                and isinstance(value, dict)
                and ("include" in value or "exclude" in value)
            ):
                # Convert dict to ChildrenSelector only if it has include/exclude keys
                merged_data[key] = ChildrenSelector(**value)
            else:
                # For all other fields, replace completely
                merged_data[key] = value

        # Create new instance with merged data
        return cls(**merged_data)


    @classmethod
    def default(cls) -> "AdapterDef":
        """Get the default definition."""
        return cls()  # Uses default field values

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the AdapterDef to a dictionary.
        """
        return asdict(self)

    def merge_with(self, other_dict: Dict[str, Any]) -> "AdapterDef":
        """
        Merge this definition with another definition dict (simple merge).

        Args:
            other_dict: Dictionary with definition overrides

        Returns:
            New AdapterDef with merged values
        """
        # Start with this definition's values (copy defaults)
        merged_data = asdict(self)

        # Simple update for each key in user-supplied dict
        for key, value in other_dict.items():
            if (
                key in merged_data
                and isinstance(merged_data[key], dict)
                and isinstance(value, dict)
            ):
                # For dict fields, update the dict (this preserves baseline values)
                merged_data[key].update(value)
            else:
                # For non-dict fields or complete replacement, just assign
                merged_data[key] = value

        return AdapterDef.from_dict(merged_data)
