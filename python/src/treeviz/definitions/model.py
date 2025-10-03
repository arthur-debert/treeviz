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
    label: str = "label"
    type: str = "type"
    children: str = "children"

    # Optional extraction mappings
    icon: Any = None
    content_lines: Any = 1
    source_location: Any = None
    metadata: Any = field(default_factory=dict)

    # Optional: Icon mappings (defaults to baseline from const.py)
    icons: Dict[str, str] = field(default_factory=lambda: ICONS.copy())

    # Optional: Per-type attribute overrides
    type_overrides: Dict[str, Dict[str, str]] = field(default_factory=dict)

    # Optional: Node types to skip during conversion
    ignore_types: List[str] = field(default_factory=list)

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
