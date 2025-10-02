"""
Declarative Converter Engine for 3viz

This module provides a declarative way to convert any tree structure to the 3viz
Node format. Instead of writing custom adapter code, users can specify how to
extract information from their AST using simple attribute mappings.

Example usage:
    config = {
        "attributes": {
            "label": "name",
            "type": "node_type",
            "children": "child_nodes"
        },
        "icon_map": {
            "paragraph": "¶",
            "list": "☰"
        }
    }
    
    node = convert_node(my_ast_node, config)
"""

import sys
from typing import Any, Dict, Optional, Callable

from .model import Node
from .exceptions import ConversionError
from .advanced_extraction import extract_attribute


def validate_config(config: Dict[str, Any]) -> None:
    """
    Validate converter configuration.

    Args:
        config: Dictionary containing attribute mappings and icon mappings

    Raises:
        ConversionError: If configuration is invalid
    """
    attributes = config.get("attributes", {})

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
    """Get the effective attribute configuration for a given node type."""
    # Start with default attributes
    effective = attributes.copy()

    # Apply type-specific overrides
    if node_type and node_type in type_overrides:
        overrides = type_overrides[node_type]
        effective.update(overrides)

    return effective


def convert_node(source_node: Any, config: Dict[str, Any]) -> Optional[Node]:
    """
    Convert a source AST node to a 3viz Node.

    Args:
        source_node: The source AST node to convert
        config: Dictionary containing attribute mappings and icon mappings

    Returns:
        3viz Node or None if node should be ignored

    Raises:
        ConversionError: If conversion fails
    """
    try:
        validate_config(config)

        attributes = config.get("attributes", {})
        icon_map = config.get("icon_map", {})
        type_overrides = config.get("type_overrides", {})
        ignore_types = set(config.get("ignore_types", []))

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
        if not icon and node_type and node_type in icon_map:
            icon = icon_map[node_type]

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
                    child_node = convert_node(child, config)
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
        # Convert any error to ConversionError for consistent handling
        if isinstance(e, ConversionError):
            raise
        else:
            raise ConversionError(f"Failed to convert node: {e}") from e


def convert_tree(source_tree: Any, config: Dict[str, Any]) -> Node:
    """
    Convenience function to convert a tree with configuration.

    Args:
        source_tree: The root of the source AST
        config: Declarative converter configuration

    Returns:
        Converted 3viz Node tree

    Raises:
        ConversionError: If conversion fails
    """
    result = convert_node(source_tree, config)

    if result is None:
        raise ConversionError(
            "Root node was ignored - check ignore_types configuration"
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


# Backward compatibility - maintain the class interface for existing code
class DeclarativeConverter:
    """
    DEPRECATED: Use convert_node() function instead.

    Converts arbitrary tree structures to 3viz Nodes using declarative configuration.
    This class is maintained for backward compatibility but will be removed in future versions.
    """

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        validate_config(config)

    def convert(self, source_node: Any) -> Optional[Node]:
        return convert_node(source_node, self.config)
