"""
Declarative Converter Engine for 3viz

This module provides a declarative way to adapt any tree structure to the 3viz
Node format. Instead of writing custom adapter code, users can specify how to
extract information from their AST using simple attribute mappings.

Example usage:
    def_ = {
        "attributes": {
            "label": "name",
            "type": "node_type",
            "children": "child_nodes"
        },
        "icons": {
            "paragraph": "¶",
            "list": "☰"
        }
    }
    
    node = adapt_node(my_ast_node, def_)
"""

import sys
from typing import Any, Dict, Optional, Callable

from .model import Node
from .exceptions import ConversionError
from .advanced_extraction import extract_attribute
from .const import ICONS


def validate_def(def_: Dict[str, Any]) -> None:
    """
    Validate converter definition.

    Args:
        def_: Dictionary containing attribute mappings and icon mappings

    Raises:
        ConversionError: If definition is invalid
    """
    attributes = def_.get("attributes", {})

    if not attributes:
        raise ConversionError("Configuration must include 'attributes' section")

    if "label" not in attributes:
        raise ConversionError(
            "Configuration must specify how to extract 'label'"
        )


def get_effective_attributes(
    attributes: Dict[str, Any],
    type_overrides: Dict[str, Any],
    node_type: Optional[str],
) -> Dict[str, Any]:
    """Get the effective attribute definition for a given node type."""
    # Start with default attributes
    effective = attributes.copy()

    # Apply type-specific overrides
    if node_type and node_type in type_overrides:
        overrides = type_overrides[node_type]
        effective.update(overrides)

    return effective


def adapt_node(source_node: Any, def_: Dict[str, Any]) -> Optional[Node]:
    """
    Adapt a source AST node to a 3viz Node.

    Args:
        source_node: The source AST node to adapt
        def_: Dictionary containing attribute mappings and icon mappings

    Returns:
        3viz Node or None if node should be ignored

    Raises:
        ConversionError: If conversion fails
    """
    try:
        validate_def(def_)

        attributes = def_.get("attributes", {})

        # Merge baseline icons with definition overrides
        icons = ICONS.copy()
        if "icons" in def_:
            icons.update(def_["icons"])

        type_overrides = def_.get("type_overrides", {})
        ignore_types = set(def_.get("ignore_types", []))

        # Check if this node type should be ignored
        node_type = extract_attribute(source_node, attributes.get("type"))
        if node_type and node_type in ignore_types:
            return None

        # Get the effective attributes for this node type
        effective_attributes = get_effective_attributes(
            attributes, type_overrides, node_type
        )

        # Extract basic attributes using advanced extractor
        label = extract_attribute(source_node, effective_attributes["label"])
        if label is None:
            label = str(node_type) if node_type else "Unknown"

        # Extract optional attributes using advanced extractor
        icon = extract_attribute(source_node, effective_attributes.get("icon"))
        content_lines = extract_attribute(
            source_node, effective_attributes.get("content_lines", 1)
        )

        if not isinstance(content_lines, int):
            content_lines = 1

        # Extract source location if configured
        source_location = None
        if "source_location" in effective_attributes:
            source_location = extract_attribute(
                source_node, effective_attributes["source_location"]
            )

        # Extract metadata using advanced extractor
        metadata = {}
        if "metadata" in effective_attributes:
            extracted_metadata = extract_attribute(
                source_node, effective_attributes["metadata"]
            )
            # Metadata can be any type after transformation (string, dict, etc.)
            metadata = (
                extracted_metadata if extracted_metadata is not None else {}
            )

        # Apply icon mapping if no explicit icon
        if not icon and node_type and node_type in icons:
            icon = icons[node_type]

        # Extract children using advanced extractor (supports filtering)
        children = []
        if "children" in effective_attributes:
            children_source = extract_attribute(
                source_node, effective_attributes["children"]
            )
            if children_source:
                if not isinstance(children_source, list):
                    raise ConversionError(
                        f"Children attribute must return a list, got {type(children_source)}"
                    )

                for child in children_source:
                    child_node = adapt_node(child, def_)
                    if child_node is not None:  # Skip ignored nodes
                        children.append(child_node)

        return Node(
            label=str(label),
            type=node_type,
            icon=icon,
            content_lines=content_lines,
            source_location=source_location,
            metadata=metadata,
            children=children,
        )

    except Exception as e:
        # Adapt any error to ConversionError for consistent handling
        if isinstance(e, ConversionError):
            raise
        else:
            raise ConversionError(f"Failed to adapt node: {e}") from e


def adapt_tree(source_tree: Any, def_: Dict[str, Any]) -> Node:
    """
    Convenience function to adapt a tree with definition.

    Args:
        source_tree: The root of the source AST
        def_: Declarative converter definition

    Returns:
        Converted 3viz Node tree

    Raises:
        ConversionError: If conversion fails
    """
    result = adapt_node(source_tree, def_)

    if result is None:
        raise ConversionError(
            "Root node was ignored - check ignore_types definition"
        )

    return result


def exit_on_error(func: Callable) -> Callable:
    """
    Decorator to exit with status 1 on ConversionError.

    This implements the "fail fast" principle - any conversion error
    should immediately exit the program with a clear error message.
    """

    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ConversionError as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)

    return wrapper
