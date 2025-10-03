"""
Definition schema for treeviz using dataclasses.

This module provides a clean, typed interface for treeviz definitions
replacing the ad-hoc dictionary validation.
"""

from dataclasses import dataclass, field, asdict
from typing import Dict, List, Any
from ..const import ICONS


@dataclass
class Definition:
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
    children: str = field(
        default="children",
        metadata={
            "doc": "Field name to extract child nodes from (e.g., 'children', 'body', 'content')"
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
    metadata: Any = field(
        default_factory=dict,
        metadata={
            "doc": "Field name for additional metadata extraction, or dict for static metadata"
        },
    )

    # Optional: Icon mappings (defaults to baseline from const.py)
    icons: Dict[str, str] = field(
        default_factory=lambda: ICONS.copy(),
        metadata={
            "doc": "Mapping from node types to Unicode icons for display"
        },
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
    def from_dict(cls, data: Dict[str, Any]) -> "Definition":
        """Create Definition from dictionary by merging with defaults."""
        # Start with default definition
        default = cls.default()
        merged_data = asdict(default)

        # Simple merge: user data overrides defaults
        for key, value in data.items():
            if (
                key == "icons"
                and isinstance(merged_data[key], dict)
                and isinstance(value, dict)
            ):
                # For icons only, merge with baseline (special case)
                merged_data[key].update(value)
            else:
                # For all other fields, replace completely
                merged_data[key] = value

        # Create new instance with merged data
        return cls(**merged_data)

    @classmethod
    def default(cls) -> "Definition":
        """Get the default definition."""
        return cls()  # Uses default field values

    def merge_with(self, other_dict: Dict[str, Any]) -> "Definition":
        """
        Merge this definition with another definition dict (simple merge).

        Args:
            other_dict: Dictionary with definition overrides

        Returns:
            New Definition with merged values
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

        return Definition.from_dict(merged_data)
