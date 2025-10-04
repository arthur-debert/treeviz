"""
3viz Data Model

This module defines the core data structures for the 3viz AST visualization tool.
The Node class is the universal tree representation for 3viz - any tool can
adapt their AST to this format for visualization.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class Node:
    """
    Core 3viz Node - the universal tree representation.

    This is the foundational data structure that any AST can be converted to
    for 3viz visualization. It's designed to be simple enough to be universal
    while rich enough to provide useful visualization information.

    The Node structure supports:
    - Visual hierarchy through children
    - Content preview through label
    - Type identification through type and icon
    - Extra extensibility
    - Source location tracking
    """

    label: str  # Display text for the node
    type: Optional[str] = None  # Node type (for icon mapping)
    icon: Optional[str] = None  # Unicode character icon
    content_lines: int = 1  # Number of lines this node represents
    source_location: Optional[Dict[str, Any]] = (
        None  # Line/column info from original source
    )
    extra: Dict[str, Any] = field(
        default_factory=dict
    )  # Extensible key-value data
    children: List["Node"] = field(default_factory=list)  # Child nodes

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Node":
        """
        Create a Node from a dictionary (e.g., from JSON deserialization).

        This handles the recursive conversion of children dictionaries to Node objects.

        Args:
            data: Dictionary containing node data

        Returns:
            Node object with properly converted children
        """
        if not isinstance(data, dict):
            raise TypeError(f"Expected dict, got {type(data)}")

        # Extract children and convert them recursively
        children_data = data.get("children", [])
        children = [cls.from_dict(child) for child in children_data]

        return cls(
            label=data.get("label", ""),
            type=data.get("type"),
            icon=data.get("icon"),
            content_lines=data.get("content_lines", 1),
            source_location=data.get("source_location"),
            extra=data.get("extra", {}),
            children=children,
        )
