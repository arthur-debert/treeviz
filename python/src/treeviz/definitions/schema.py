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

    # Required: How to extract core node properties
    attributes: Dict[str, str] = field(
        default_factory=lambda: {
            "label": "label",
            "type": "type",
            "children": "children",
        }
    )

    # Optional: Icon mappings (merged with baseline from const.py)
    icons: Dict[str, str] = field(default_factory=dict)

    # Optional: Per-type attribute overrides
    type_overrides: Dict[str, Dict[str, str]] = field(default_factory=dict)

    # Optional: Node types to skip during conversion
    ignore_types: List[str] = field(default_factory=list)

    def __post_init__(self):
        """Validate definition after creation."""
        self._validate()

    def _validate(self):
        """Validate the definition structure."""
        # Check required attributes section
        if not isinstance(self.attributes, dict):
            raise TypeError(
                "'attributes' section must be a dictionary. "
                "Example: {'attributes': {'label': 'name', 'type': 'node_type', 'children': 'children'}}"
            )

        if "label" not in self.attributes:
            raise KeyError(
                "'attributes' must specify how to extract 'label'. "
                "Example: {'attributes': {'label': 'name', 'type': 'node_type'}}. "
                "See treeviz documentation for more details."
            )

        # Check optional sections
        if not isinstance(self.icons, dict):
            raise TypeError(
                "'icons' must be a dictionary. "
                "Example: {'icons': {'paragraph': '¶', 'heading': '⊤'}}"
            )

        if not isinstance(self.type_overrides, dict):
            raise TypeError(
                "'type_overrides' must be a dictionary. "
                "Example: {'type_overrides': {'paragraph': {'label': 'content'}}}"
            )

        if not isinstance(self.ignore_types, list):
            raise TypeError(
                "'ignore_types' must be a list. "
                "Example: {'ignore_types': ['comment', 'whitespace']}"
            )

        # Validate type_overrides structure
        for type_name, overrides in self.type_overrides.items():
            if not isinstance(overrides, dict):
                raise TypeError(
                    f"Type override for '{type_name}' must be a dictionary. "
                    f"Example: {{'type_overrides': {{'{type_name}': {{'label': 'custom_field'}}}}}}"
                )

    def to_dict(self, merge_icons: bool = True) -> Dict[str, Any]:
        """Convert to dictionary format (for compatibility/serialization)."""
        result = asdict(self)

        if merge_icons:
            # Merge baseline icons with definition overrides
            merged_icons = ICONS.copy()
            merged_icons.update(result["icons"])
            result["icons"] = merged_icons

        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Definition":
        """Create Definition from dictionary (parsing/validation)."""
        if not isinstance(data, dict):
            raise TypeError(
                "Definition must be a dictionary. "
                "Example: {'attributes': {'label': 'name', 'type': 'node_type'}}"
            )

        # Check if attributes section exists
        if "attributes" not in data:
            raise KeyError(
                "Configuration must include 'attributes' section. "
                "Example: {'attributes': {'label': 'name', 'type': 'node_type', 'children': 'children'}}. "
                "See treeviz documentation for complete schema."
            )

        # Extract known fields, ignore unknown ones
        attributes = data.get("attributes", {})
        icons = data.get("icons", {})
        type_overrides = data.get("type_overrides", {})
        ignore_types = data.get("ignore_types", [])

        return cls(
            attributes=attributes,
            icons=icons,
            type_overrides=type_overrides,
            ignore_types=ignore_types,
        )

    @classmethod
    def default(cls) -> "Definition":
        """Get the default definition."""
        return cls()  # Uses default field values

    def merge_with(self, other_dict: Dict[str, Any]) -> "Definition":
        """
        Merge this definition with another definition dict (deep merge).

        Args:
            other_dict: Dictionary with definition overrides

        Returns:
            New Definition with merged values
        """
        # Start with this definition's values
        merged_attributes = self.attributes.copy()
        merged_icons = self.icons.copy()
        merged_type_overrides = self.type_overrides.copy()
        merged_ignore_types = self.ignore_types.copy()

        # Deep merge attributes
        if "attributes" in other_dict and isinstance(
            other_dict["attributes"], dict
        ):
            merged_attributes.update(other_dict["attributes"])

        # Merge icons
        if "icons" in other_dict and isinstance(other_dict["icons"], dict):
            merged_icons.update(other_dict["icons"])

        # Deep merge type_overrides
        if "type_overrides" in other_dict and isinstance(
            other_dict["type_overrides"], dict
        ):
            for type_name, overrides in other_dict["type_overrides"].items():
                if type_name in merged_type_overrides and isinstance(
                    overrides, dict
                ):
                    merged_type_overrides[type_name] = {
                        **merged_type_overrides[type_name],
                        **overrides,
                    }
                else:
                    merged_type_overrides[type_name] = overrides

        # Replace ignore_types (list replacement, not merge)
        if "ignore_types" in other_dict and isinstance(
            other_dict["ignore_types"], list
        ):
            merged_ignore_types = other_dict["ignore_types"].copy()

        return Definition(
            attributes=merged_attributes,
            icons=merged_icons,
            type_overrides=merged_type_overrides,
            ignore_types=merged_ignore_types,
        )

    def get_merged_icons(self) -> Dict[str, str]:
        """Get icons merged with baseline from const.py."""
        merged = ICONS.copy()
        merged.update(self.icons)
        return merged
